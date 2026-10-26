"""Retry Logic with Exponential Backoff.

Provides sophisticated retry mechanisms for GraphQL client operations
with exponential backoff, jitter, and circuit breaker patterns.
"""

import asyncio
import logging
import secrets
import time
from dataclasses import dataclass
from enum import Enum

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.fraiseql_client import (
    AuthenticationError,
    FraiseQLClient,
    GraphQLClientError,
    GraphQLResponse,
    NetworkError,
)

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_timeout: bool = True
    retry_on_network_error: bool = True
    retry_on_server_error: bool = True
    retry_on_auth_error: bool = False


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 3


class CircuitBreaker:
    """Circuit breaker implementation to prevent cascade failures.

    Tracks failures and opens the circuit when failure threshold is reached,
    preventing further requests until recovery timeout expires.
    """

    def __init__(self, config: CircuitBreakerConfig):
        """Initialize circuit breaker."""
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0

    def is_request_allowed(self) -> bool:
        """Check if request is allowed through the circuit."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Record a successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self):
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker returned to OPEN state")


class RetryableClient:
    """GraphQL client with retry logic and circuit breaker.

    Wraps the base FraiseQLClient to provide resilient operations
    with exponential backoff, jitter, and circuit breaker protection.
    """

    def __init__(
        self,
        client: FraiseQLClient,
        retry_config: RetryConfig | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ):
        """Initialize retryable client.

        Args:
        ----
            client: Base FraiseQL client
            retry_config: Retry behavior configuration
            circuit_breaker_config: Circuit breaker configuration

        """
        self.client = client
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config or CircuitBreakerConfig())

    async def execute_query(
        self,
        query: str,
        variables: dict | None = None,
        operation_name: str | None = None,
        timeout: int | None = None,
        retry_config: RetryConfig | None = None,
    ) -> GraphQLResponse:
        """Execute GraphQL query with retry logic.

        Args:
        ----
            query: GraphQL query string
            variables: Optional query variables
            operation_name: Optional operation name
            timeout: Optional timeout override
            retry_config: Optional retry config override

        Returns:
        -------
            GraphQLResponse from successful execution

        Raises:
        ------
            GraphQLClientError: After all retries exhausted

        """
        config = retry_config or self.retry_config
        attempt = 0
        last_exception = None

        while attempt <= config.max_retries:
            # Check circuit breaker
            if not self.circuit_breaker.is_request_allowed():
                raise GraphQLClientError(
                    "Circuit breaker is OPEN - service unavailable", status_code=503
                )

            try:
                # Execute the query
                response = await self.client.execute_query(
                    query=query, variables=variables, operation_name=operation_name, timeout=timeout
                )

                # Success - record with circuit breaker
                self.circuit_breaker.record_success()
                logger.debug(f"Query succeeded on attempt {attempt + 1}")
                return response

            except Exception as e:
                last_exception = e
                attempt += 1

                # Check if we should retry this error
                if not self._should_retry(e, config):
                    logger.debug(f"Not retrying error: {type(e).__name__}: {e}")
                    self.circuit_breaker.record_failure()
                    raise e

                # Check if we have retries left
                if attempt > config.max_retries:
                    logger.warning(f"Max retries ({config.max_retries}) exceeded")
                    self.circuit_breaker.record_failure()
                    break

                # Calculate delay and wait
                delay = self._calculate_delay(attempt - 1, config)
                logger.info(
                    f"Attempt {attempt} failed: {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )

                await asyncio.sleep(delay)

        # All retries exhausted
        self.circuit_breaker.record_failure()
        raise last_exception or GraphQLClientError("All retries exhausted")

    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """Determine if an exception should trigger a retry."""
        if isinstance(exception, NetworkError):
            # Check if it's a timeout error
            if "timeout" in str(exception).lower():
                return config.retry_on_timeout
            return config.retry_on_network_error

        if isinstance(exception, AuthenticationError):
            return config.retry_on_auth_error

        if isinstance(exception, GraphQLClientError):
            # Retry on server errors (5xx)
            if hasattr(exception, "status_code") and exception.status_code:
                if 500 <= exception.status_code < 600:
                    return config.retry_on_server_error
                # Don't retry client errors (4xx)
                if 400 <= exception.status_code < 500:
                    return False
            return True

        # For other exceptions, don't retry by default
        return False

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for exponential backoff with jitter."""
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = config.base_delay * (config.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, config.max_delay)

        # Add jitter to prevent thundering herd
        if config.jitter:
            # Use cryptographically secure random for jitter
            secure_random = secrets.SystemRandom()
            delay = delay * (0.5 + secure_random.random() * 0.5)

        return delay

    def get_circuit_breaker_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "state": self.circuit_breaker.state.value,
            "failure_count": self.circuit_breaker.failure_count,
            "success_count": self.circuit_breaker.success_count,
            "last_failure_time": self.circuit_breaker.last_failure_time,
        }

    def reset_circuit_breaker(self):
        """Reset circuit breaker to closed state."""
        self.circuit_breaker.state = CircuitState.CLOSED
        self.circuit_breaker.failure_count = 0
        self.circuit_breaker.success_count = 0
        self.circuit_breaker.last_failure_time = 0.0
        logger.info("Circuit breaker manually reset to CLOSED")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self.client, "__aexit__"):
            await self.client.__aexit__(exc_type, exc_val, exc_tb)


def create_retryable_client(
    endpoint: Endpoint,
    retry_config: RetryConfig | None = None,
    circuit_breaker_config: CircuitBreakerConfig | None = None,
) -> RetryableClient:
    """Create a retryable client from endpoint configuration.

    Args:
    ----
        endpoint: Endpoint configuration
        retry_config: Optional retry configuration
        circuit_breaker_config: Optional circuit breaker configuration

    Returns:
    -------
        Configured RetryableClient instance

    """
    # Create base client
    base_client = FraiseQLClient(endpoint)

    # Use endpoint configuration for retry settings if not provided
    if retry_config is None:
        retry_config = RetryConfig(
            max_retries=endpoint.max_retries,
            base_delay=endpoint.retry_delay_seconds,
        )

    return RetryableClient(
        client=base_client, retry_config=retry_config, circuit_breaker_config=circuit_breaker_config
    )

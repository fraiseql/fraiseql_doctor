"""Advanced retry logic with circuit breaker pattern."""
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Dict
from dataclasses import dataclass

from fraiseql_doctor.core.exceptions import CircuitBreakerOpenError
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.client import FraiseQLClient, GraphQLResponse


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    expected_exception: type = Exception
    

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    success_count: int = 0
    total_requests: int = 0


class CircuitBreaker:
    """Circuit breaker for GraphQL client."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.stats = CircuitBreakerStats()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        self.stats.total_requests += 1
        
        if self.stats.state == CircuitState.OPEN:
            if time.time() - self.stats.last_failure_time > self.config.recovery_timeout:
                self.stats.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.config.expected_exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self) -> None:
        """Handle successful request."""
        self.stats.success_count += 1
        self.stats.failure_count = 0
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.state = CircuitState.CLOSED
    
    async def _on_failure(self) -> None:
        """Handle failed request."""
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()
        
        if self.stats.failure_count >= self.config.failure_threshold:
            self.stats.state = CircuitState.OPEN
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "last_failure_time": self.stats.last_failure_time,
            "success_rate": (
                self.stats.success_count / self.stats.total_requests * 100
                if self.stats.total_requests > 0 else 0
            )
        }
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.stats = CircuitBreakerStats()


class RetryableClient:
    """GraphQL client with retry logic and circuit breaker."""
    
    def __init__(self, client: FraiseQLClient, endpoint: Endpoint):
        self.client = client
        self.endpoint = endpoint
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=(endpoint.max_retries or 3) + 2,  # Allow retries before opening
            recovery_timeout=60
        ))
    
    async def execute_with_retry(
        self,
        query: str,
        variables: Dict[str, Any] | None = None,
        **kwargs
    ) -> GraphQLResponse:
        """Execute query with retry logic and circuit breaker."""
        max_retries = self.endpoint.max_retries or 3
        base_delay = 1  # Default retry delay in seconds
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.circuit_breaker.call(
                    self.client.execute_query,
                    query,
                    variables,
                    **kwargs
                )
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    # All retries exhausted
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = self._calculate_delay(base_delay, attempt)
                await asyncio.sleep(delay)
        
        # Re-raise the last exception if all retries failed
        if last_exception:
            raise last_exception
        
        # This should never be reached
        raise Exception("Unexpected retry logic error")
    
    def _calculate_delay(self, base_delay: float, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter."""
        # Exponential backoff
        delay = base_delay * (2 ** attempt)
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.1, 0.3) * delay
        
        # Cap maximum delay
        max_delay = 60.0
        return min(delay + jitter, max_delay)
    
    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        from fraiseql_doctor.core.exceptions import (
            GraphQLTimeoutError,
            GraphQLClientError,
            GraphQLAuthError
        )
        
        # Don't retry authentication errors
        if isinstance(exception, GraphQLAuthError):
            return False
        
        # Retry timeout and general client errors
        if isinstance(exception, (GraphQLTimeoutError, GraphQLClientError)):
            return True
        
        # Retry on network-related errors
        if isinstance(exception, (asyncio.TimeoutError, ConnectionError)):
            return True
        
        return False
    
    async def health_check_with_retry(self) -> Dict[str, Any]:
        """Perform health check with retry logic."""
        try:
            result = await self.execute_with_retry("query { __typename }")
            return {
                "healthy": True,
                "response_time_ms": result.response_time_ms,
                "circuit_breaker": self.circuit_breaker.get_stats()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "circuit_breaker": self.circuit_breaker.get_stats()
            }
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return self.circuit_breaker.get_stats()
    
    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state."""
        self.circuit_breaker.reset()
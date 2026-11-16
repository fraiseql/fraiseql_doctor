"""Test module for retry logic and circuit breaker functionality.

Tests the retry mechanisms, exponential backoff, and circuit breaker patterns.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.fraiseql_client import (
    AuthenticationError,
    FraiseQLClient,
    GraphQLClientError,
    GraphQLResponse,
    NetworkError,
)
from fraiseql_doctor.services.retry import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    RetryableClient,
    RetryConfig,
    create_retryable_client,
)


class TestRetryConfig:
    """Test retry configuration."""

    def test_default_config(self):
        """Test default retry configuration values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.retry_on_timeout is True
        assert config.retry_on_network_error is True
        assert config.retry_on_server_error is True
        assert config.retry_on_auth_error is False

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False,
            retry_on_auth_error=True,
        )

        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False
        assert config.retry_on_auth_error is True


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_initial_state(self):
        """Test circuit breaker initial state."""
        config = CircuitBreakerConfig()
        breaker = CircuitBreaker(config)

        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.is_request_allowed() is True

    def test_failure_threshold(self):
        """Test circuit opens after failure threshold."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        # Record failures up to threshold
        for i in range(3):
            assert breaker.state == CircuitState.CLOSED
            breaker.record_failure()

        # Should open after threshold
        assert breaker.state == CircuitState.OPEN
        assert breaker.is_request_allowed() is False

    def test_recovery_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # 100ms for testing
        )
        breaker = CircuitBreaker(config)

        # Trigger circuit open
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Should still be open immediately
        assert breaker.is_request_allowed() is False

        # Wait for recovery timeout
        time.sleep(0.15)

        # Should transition to half-open
        assert breaker.is_request_allowed() is True
        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_success_recovery(self):
        """Test circuit closes after successful operations in half-open state."""
        config = CircuitBreakerConfig(
            failure_threshold=2, success_threshold=2, recovery_timeout=0.1
        )
        breaker = CircuitBreaker(config)

        # Trigger circuit open
        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)

        # Transition to half-open
        breaker.is_request_allowed()
        assert breaker.state == CircuitState.HALF_OPEN

        # Record successful operations
        breaker.record_success()
        assert breaker.state == CircuitState.HALF_OPEN

        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_failure_returns_to_open(self):
        """Test circuit returns to open on failure in half-open state."""
        config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.1)
        breaker = CircuitBreaker(config)

        # Trigger circuit open
        breaker.record_failure()
        breaker.record_failure()
        time.sleep(0.15)

        # Transition to half-open
        breaker.is_request_allowed()
        assert breaker.state == CircuitState.HALF_OPEN

        # Record failure - should return to open
        breaker.record_failure()
        assert breaker.state == CircuitState.OPEN


class TestRetryableClient:
    """Test retryable client functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.endpoint = Endpoint(
            pk_endpoint="test-id",
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
            auth_config={},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        self.mock_client = Mock(spec=FraiseQLClient)
        self.mock_client.execute_query = AsyncMock()

        self.retry_config = RetryConfig(
            max_retries=2,
            base_delay=0.1,  # Fast for testing
            jitter=False,  # Predictable for testing
        )

        self.retryable_client = RetryableClient(
            client=self.mock_client, retry_config=self.retry_config
        )

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful query execution without retries."""
        expected_response = GraphQLResponse(data={"test": "success"}, response_time_ms=100)
        self.mock_client.execute_query.return_value = expected_response

        response = await self.retryable_client.execute_query("query { test }")

        assert response == expected_response
        assert self.mock_client.execute_query.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """Test retry behavior on network errors."""
        # First two calls fail, third succeeds
        self.mock_client.execute_query.side_effect = [
            NetworkError("Connection failed"),
            NetworkError("Connection failed"),
            GraphQLResponse(data={"test": "success"}, response_time_ms=100),
        ]

        start_time = time.time()
        response = await self.retryable_client.execute_query("query { test }")
        end_time = time.time()

        assert response.data == {"test": "success"}
        assert self.mock_client.execute_query.call_count == 3

        # Should have waited for delays (0.1s + 0.2s = 0.3s minimum)
        assert end_time - start_time >= 0.3

    @pytest.mark.asyncio
    async def test_no_retry_on_auth_error_by_default(self):
        """Test that auth errors are not retried by default."""
        self.mock_client.execute_query.side_effect = AuthenticationError(
            "Invalid token", status_code=401
        )

        with pytest.raises(AuthenticationError):
            await self.retryable_client.execute_query("query { test }")

        # Should not retry auth errors
        assert self.mock_client.execute_query.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_auth_error_when_configured(self):
        """Test auth error retry when explicitly configured."""
        config = RetryConfig(max_retries=2, retry_on_auth_error=True, base_delay=0.1)
        client = RetryableClient(self.mock_client, config)

        self.mock_client.execute_query.side_effect = [
            AuthenticationError("Invalid token", status_code=401),
            AuthenticationError("Invalid token", status_code=401),
            GraphQLResponse(data={"test": "success"}, response_time_ms=100),
        ]

        response = await client.execute_query("query { test }")

        assert response.data == {"test": "success"}
        assert self.mock_client.execute_query.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self):
        """Test that 4xx client errors are not retried."""
        self.mock_client.execute_query.side_effect = GraphQLClientError(
            "Bad request", status_code=400
        )

        with pytest.raises(GraphQLClientError):
            await self.retryable_client.execute_query("query { test }")

        # Should not retry client errors
        assert self.mock_client.execute_query.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self):
        """Test retry behavior on 5xx server errors."""
        self.mock_client.execute_query.side_effect = [
            GraphQLClientError("Internal server error", status_code=500),
            GraphQLResponse(data={"test": "success"}, response_time_ms=100),
        ]

        response = await self.retryable_client.execute_query("query { test }")

        assert response.data == {"test": "success"}
        assert self.mock_client.execute_query.call_count == 2

    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test behavior when max retries are exhausted."""
        self.mock_client.execute_query.side_effect = NetworkError("Connection failed")

        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        # Should try initial + max_retries (1 + 2 = 3)
        assert self.mock_client.execute_query.call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(max_retries=3, base_delay=0.1, exponential_base=2.0, jitter=False)
        client = RetryableClient(self.mock_client, config)

        # Calculate expected delays
        delay_0 = client._calculate_delay(0, config)  # 0.1 * 2^0 = 0.1
        delay_1 = client._calculate_delay(1, config)  # 0.1 * 2^1 = 0.2
        delay_2 = client._calculate_delay(2, config)  # 0.1 * 2^2 = 0.4

        assert delay_0 == 0.1
        assert delay_1 == 0.2
        assert delay_2 == 0.4

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        config = RetryConfig(base_delay=10.0, max_delay=5.0, exponential_base=2.0, jitter=False)
        client = RetryableClient(self.mock_client, config)

        # Large attempt should be capped
        delay = client._calculate_delay(10, config)
        assert delay == 5.0

    @pytest.mark.asyncio
    async def test_jitter_variation(self):
        """Test that jitter adds randomness to delays."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=True)
        client = RetryableClient(self.mock_client, config)

        # Run multiple times to check variation
        delays = [client._calculate_delay(1, config) for _ in range(10)]

        # Should be between 1.0 and 2.0 (0.5 * 2.0 to 1.0 * 2.0)
        for delay in delays:
            assert 1.0 <= delay <= 2.0

        # Should have some variation
        assert len(set(delays)) > 1


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with retryable client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock(spec=FraiseQLClient)
        self.mock_client.execute_query = AsyncMock()

        self.circuit_config = CircuitBreakerConfig(
            failure_threshold=4,  # Higher threshold to allow for retries
            recovery_timeout=0.1,
            success_threshold=1,
        )

        self.retryable_client = RetryableClient(
            client=self.mock_client,
            retry_config=RetryConfig(max_retries=1, base_delay=0.01),
            circuit_breaker_config=self.circuit_config,
        )

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit breaker opens after failure threshold."""
        self.mock_client.execute_query.side_effect = NetworkError("Connection failed")

        # Execute queries to reach failure threshold (4 failures)
        # Each query attempt will fail twice (original + 1 retry)
        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        # Circuit should now be open (4 total failures: 2 queries × 2 attempts each)
        status = self.retryable_client.get_circuit_breaker_status()
        assert status["state"] == "open"

        # Next query should be blocked by circuit breaker
        with pytest.raises(GraphQLClientError) as exc_info:
            await self.retryable_client.execute_query("query { test }")

        assert "Circuit breaker is OPEN" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        self.mock_client.execute_query.side_effect = NetworkError("Connection failed")

        # Trigger circuit open (need 4 failures)
        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Should allow request and transition to half-open
        self.mock_client.execute_query.side_effect = None
        self.mock_client.execute_query.return_value = GraphQLResponse(
            data={"test": "success"}, response_time_ms=100
        )

        response = await self.retryable_client.execute_query("query { test }")

        assert response.data == {"test": "success"}

        # Circuit should be closed after successful operation
        status = self.retryable_client.get_circuit_breaker_status()
        assert status["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset."""
        self.mock_client.execute_query.side_effect = NetworkError("Connection failed")

        # Trigger circuit open (need 4 failures)
        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        with pytest.raises(NetworkError):
            await self.retryable_client.execute_query("query { test }")

        # Manually reset
        self.retryable_client.reset_circuit_breaker()

        status = self.retryable_client.get_circuit_breaker_status()
        assert status["state"] == "closed"
        assert status["failure_count"] == 0


class TestRetryableClientCreation:
    """Test retryable client creation from endpoint."""

    def test_create_from_endpoint(self):
        """Test creating retryable client from endpoint configuration."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            auth_type="bearer",
            auth_config={"token": "test-token"},
            timeout_seconds=30,
            max_retries=5,
            retry_delay_seconds=2.0,
        )

        client = create_retryable_client(endpoint)

        assert isinstance(client, RetryableClient)
        assert isinstance(client.client, FraiseQLClient)
        assert client.retry_config.max_retries == 5
        assert client.retry_config.base_delay == 2.0
        assert client.client.endpoint == endpoint

    def test_create_with_custom_configs(self):
        """Test creating retryable client with custom configurations."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
            auth_config={},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        retry_config = RetryConfig(max_retries=10, base_delay=0.5)
        circuit_config = CircuitBreakerConfig(failure_threshold=10)

        client = create_retryable_client(
            endpoint=endpoint, retry_config=retry_config, circuit_breaker_config=circuit_config
        )

        assert client.retry_config.max_retries == 10
        assert client.retry_config.base_delay == 0.5
        assert client.circuit_breaker.config.failure_threshold == 10


class TestAsyncContextManager:
    """Test async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager usage."""
        mock_client = Mock(spec=FraiseQLClient)
        mock_client.__aexit__ = AsyncMock()

        retryable_client = RetryableClient(mock_client)

        async with retryable_client as client:
            assert client == retryable_client

        # Should call underlying client's __aexit__
        mock_client.__aexit__.assert_called_once()

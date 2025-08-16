"""Tests for FraiseQL client infrastructure."""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
import aiohttp
from aioresponses import aioresponses

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.client import FraiseQLClient, GraphQLResponse
from fraiseql_doctor.services.auth import BearerTokenAuth, APIKeyAuth, BasicAuth, create_auth_provider
from fraiseql_doctor.services.complexity import QueryComplexityAnalyzer, ComplexityMetrics
from fraiseql_doctor.services.pool import ConnectionPoolManager
from fraiseql_doctor.services.retry import RetryableClient, CircuitBreaker, CircuitBreakerConfig
from fraiseql_doctor.services.metrics import MetricsCollector, QueryMetrics
from fraiseql_doctor.core.exceptions import (
    GraphQLClientError, 
    GraphQLTimeoutError, 
    GraphQLAuthError,
    CircuitBreakerOpenError
)


class TestFraiseQLClient:
    """Test the base FraiseQL client."""
    
    @pytest.fixture
    def sample_endpoint(self):
        """Sample endpoint for testing."""
        from fraiseql_doctor.models.endpoint import AuthType
        return Endpoint(
            id=uuid4(),
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            auth_type=AuthType.BEARER,
            auth_config={"token": "test-token"},
            headers={"Custom-Header": "value"},
            timeout_seconds=30,
            max_retries=3,
            is_active=True
        )
    
    @pytest.fixture
    async def client(self, sample_endpoint):
        """Create a test client."""
        session = aiohttp.ClientSession()
        client = FraiseQLClient(sample_endpoint, session)
        yield client
        await session.close()
    
    async def test_execute_query_success(self, client):
        """Test successful query execution."""
        query = "query { user { id name } }"
        
        with aioresponses() as m:
            m.post(
                str(client.endpoint.url),
                payload={
                    "data": {"user": {"id": "1", "name": "Test User"}},
                    "extensions": {"complexity": 10}
                }
            )
            
            response = await client.execute_query(query)
            
            assert response.data == {"user": {"id": "1", "name": "Test User"}}
            assert response.errors is None
            assert response.complexity_score == 10
            assert response.response_time_ms > 0
    
    async def test_execute_query_with_errors(self, client):
        """Test query execution with GraphQL errors."""
        query = "query { invalidField }"
        
        with aioresponses() as m:
            m.post(
                str(client.endpoint.url),
                payload={
                    "data": None,
                    "errors": [{"message": "Field 'invalidField' not found"}]
                }
            )
            
            response = await client.execute_query(query)
            
            assert response.data is None
            assert len(response.errors) == 1
            assert "invalidField" in response.errors[0]["message"]
    
    async def test_execute_query_timeout(self, client):
        """Test query timeout handling."""
        query = "query { user { id } }"
        
        with aioresponses() as m:
            m.post(str(client.endpoint.url), exception=asyncio.TimeoutError())
            
            with pytest.raises(GraphQLTimeoutError) as exc_info:
                await client.execute_query(query, timeout=1)
            
            assert "timeout" in str(exc_info.value).lower()
            assert exc_info.value.response_time_ms > 0
    
    async def test_execute_query_auth_error(self, client):
        """Test authentication error handling."""
        query = "query { user { id } }"
        
        with aioresponses() as m:
            m.post(str(client.endpoint.url), status=401, payload={"error": "Unauthorized"})
            
            with pytest.raises(GraphQLAuthError):
                await client.execute_query(query)
    
    async def test_health_check(self, client):
        """Test health check functionality."""
        with aioresponses() as m:
            m.post(
                str(client.endpoint.url),
                payload={"data": {"__typename": "Query"}}
            )
            
            result = await client.health_check()
            
            assert result["healthy"] is True
            assert result["response_time_ms"] > 0
            assert result["errors"] is None


class TestAuthProviders:
    """Test authentication providers."""
    
    async def test_bearer_token_auth(self):
        """Test bearer token authentication."""
        auth = BearerTokenAuth("test-token")
        
        headers = await auth.get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        
        is_valid = await auth.is_valid()
        assert is_valid is True
    
    async def test_api_key_auth(self):
        """Test API key authentication."""
        auth = APIKeyAuth("test-key", "X-Custom-Key")
        
        headers = await auth.get_headers()
        assert headers["X-Custom-Key"] == "test-key"
        
        is_valid = await auth.is_valid()
        assert is_valid is True
    
    async def test_basic_auth(self):
        """Test basic authentication."""
        auth = BasicAuth("username", "password")
        
        headers = await auth.get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        
        is_valid = await auth.is_valid()
        assert is_valid is True
    
    def test_create_auth_provider_bearer(self):
        """Test auth provider factory for bearer token."""
        from fraiseql_doctor.models.endpoint import AuthType
        endpoint = Endpoint(
            id=uuid4(),
            name="Test",
            url="https://example.com/graphql",
            auth_type=AuthType.BEARER,
            auth_config={"token": "test-token"}
        )
        
        auth = create_auth_provider(endpoint)
        assert isinstance(auth, BearerTokenAuth)
    
    def test_create_auth_provider_none(self):
        """Test auth provider factory for no auth."""
        from fraiseql_doctor.models.endpoint import AuthType
        endpoint = Endpoint(
            id=uuid4(),
            name="Test",
            url="https://example.com/graphql",
            auth_type=AuthType.NONE
        )
        
        auth = create_auth_provider(endpoint)
        assert auth is not None  # Returns NoAuth instance


class TestQueryComplexityAnalyzer:
    """Test query complexity analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return QueryComplexityAnalyzer(max_depth=5, max_complexity=100)
    
    def test_simple_query_analysis(self, analyzer):
        """Test analysis of a simple query."""
        query = "query { user { id name } }"
        
        metrics = analyzer.analyze_query(query)
        
        assert isinstance(metrics, ComplexityMetrics)
        assert metrics.depth > 0
        assert metrics.field_count > 0
        assert metrics.total_score > 0
    
    def test_complex_query_analysis(self, analyzer):
        """Test analysis of a complex query."""
        query = """
        query {
            users {
                id
                name
                posts {
                    id
                    title
                    comments {
                        id
                        content
                        author {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        
        metrics = analyzer.analyze_query(query)
        
        assert metrics.depth >= 4
        assert metrics.field_count >= 8
        assert len(metrics.recommendations) > 0
    
    def test_query_validation(self, analyzer):
        """Test query validation against limits."""
        simple_query = "query { user { id } }"
        complex_query = "query { " + "user { " * 10 + "id" + " }" * 10 + " }"
        
        simple_result = analyzer.validate_query_limits(simple_query)
        complex_result = analyzer.validate_query_limits(complex_query)
        
        assert simple_result["valid"] is True
        assert len(simple_result["violations"]) == 0
        
        assert complex_result["valid"] is False
        assert len(complex_result["violations"]) > 0


class TestConnectionPoolManager:
    """Test connection pool management."""
    
    @pytest.fixture
    async def pool_manager(self):
        """Create pool manager instance."""
        manager = ConnectionPoolManager(max_connections_per_endpoint=5)
        yield manager
        await manager.close_all()
    
    @pytest.fixture
    def sample_endpoint(self):
        """Sample endpoint for testing."""
        return Endpoint(
            id=uuid4(),
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            timeout_seconds=30
        )
    
    async def test_get_session(self, pool_manager, sample_endpoint):
        """Test getting a session for an endpoint."""
        session = await pool_manager.get_session(sample_endpoint)
        
        assert isinstance(session, aiohttp.ClientSession)
        assert not session.closed
    
    async def test_session_reuse(self, pool_manager, sample_endpoint):
        """Test that sessions are reused for the same endpoint."""
        session1 = await pool_manager.get_session(sample_endpoint)
        session2 = await pool_manager.get_session(sample_endpoint)
        
        assert session1 is session2
    
    async def test_close_session(self, pool_manager, sample_endpoint):
        """Test closing a specific session."""
        session = await pool_manager.get_session(sample_endpoint)
        endpoint_id = sample_endpoint.id
        
        await pool_manager.close_session(endpoint_id)
        
        assert endpoint_id not in pool_manager
    
    async def test_pool_stats(self, pool_manager, sample_endpoint):
        """Test getting pool statistics."""
        await pool_manager.get_session(sample_endpoint)
        
        stats = await pool_manager.get_pool_stats()
        
        assert stats["total_pools"] == 1
        assert len(stats["pools"]) == 1


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker instance."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1)
        return CircuitBreaker(config)
    
    async def test_successful_call(self, circuit_breaker):
        """Test successful function call through circuit breaker."""
        async def success_func():
            return "success"
        
        result = await circuit_breaker.call(success_func)
        assert result == "success"
        assert circuit_breaker.stats.success_count == 1
    
    async def test_failure_handling(self, circuit_breaker):
        """Test failure handling and circuit opening."""
        async def failing_func():
            raise Exception("Test error")
        
        # Trigger failures to open circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Circuit should now be open
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(failing_func)
    
    async def test_recovery(self, circuit_breaker):
        """Test circuit breaker recovery."""
        async def failing_func():
            raise Exception("Test error")
        
        async def success_func():
            return "success"
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_func)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Should allow one call (half-open)
        result = await circuit_breaker.call(success_func)
        assert result == "success"


class TestMetricsCollector:
    """Test metrics collection and analysis."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector instance."""
        return MetricsCollector(max_metrics=100)
    
    @pytest.fixture
    def sample_metrics(self):
        """Sample query metrics."""
        return QueryMetrics(
            query_id="test123",
            endpoint_id="endpoint1",
            operation_name="GetUser",
            execution_time_ms=250,
            response_size_bytes=1024,
            complexity_score=50,
            success=True
        )
    
    def test_record_query(self, metrics_collector, sample_metrics):
        """Test recording query metrics."""
        metrics_collector.record_query(sample_metrics)
        
        assert len(metrics_collector.metrics) == 1
        assert metrics_collector.metrics[0] == sample_metrics
    
    def test_performance_summary(self, metrics_collector):
        """Test performance summary generation."""
        # Add some test metrics
        for i in range(5):
            metrics = QueryMetrics(
                query_id=f"test{i}",
                endpoint_id="endpoint1",
                operation_name="GetUser",
                execution_time_ms=100 + i * 50,
                response_size_bytes=1024,
                complexity_score=50,
                success=i < 4  # One failure
            )
            metrics_collector.record_query(metrics)
        
        summary = metrics_collector.get_performance_summary("endpoint1")
        
        assert summary["total_queries"] == 5
        assert summary["successful_queries"] == 4
        assert summary["failed_queries"] == 1
        assert summary["success_rate"] == 80.0
        assert summary["avg_response_time_ms"] > 0
    
    def test_slow_queries(self, metrics_collector):
        """Test slow query detection."""
        # Add fast and slow queries
        fast_metrics = QueryMetrics(
            query_id="fast",
            endpoint_id="endpoint1", 
            operation_name="FastQuery",
            execution_time_ms=50,
            response_size_bytes=512,
            complexity_score=10,
            success=True
        )
        
        slow_metrics = QueryMetrics(
            query_id="slow",
            endpoint_id="endpoint1",
            operation_name="SlowQuery", 
            execution_time_ms=2000,
            response_size_bytes=2048,
            complexity_score=100,
            success=True
        )
        
        metrics_collector.record_query(fast_metrics)
        metrics_collector.record_query(slow_metrics)
        
        slow_queries = metrics_collector.get_slow_queries(threshold_ms=1000)
        
        assert len(slow_queries) == 1
        assert slow_queries[0]["query_id"] == "slow"
        assert slow_queries[0]["execution_time_ms"] == 2000


class TestRetryableClient:
    """Test retryable client functionality."""
    
    @pytest.fixture
    def sample_endpoint(self):
        """Sample endpoint for testing."""
        return Endpoint(
            id=uuid4(),
            name="Test Endpoint",
            url="https://api.example.com/graphql",
            max_retries=2
        )
    
    @pytest.fixture
    async def base_client(self, sample_endpoint):
        """Create base client mock."""
        client = Mock(spec=FraiseQLClient)
        client.endpoint = sample_endpoint
        return client
    
    @pytest.fixture
    def retryable_client(self, base_client, sample_endpoint):
        """Create retryable client."""
        return RetryableClient(base_client, sample_endpoint)
    
    async def test_successful_execution(self, retryable_client, base_client):
        """Test successful query execution."""
        response = GraphQLResponse(
            data={"user": {"id": "1"}},
            response_time_ms=100
        )
        base_client.execute_query = AsyncMock(return_value=response)
        
        result = await retryable_client.execute_with_retry("query { user { id } }")
        
        assert result.data == {"user": {"id": "1"}}
        assert base_client.execute_query.call_count == 1
    
    async def test_retry_on_failure(self, retryable_client, base_client):
        """Test retry logic on failures."""
        # First two calls fail, third succeeds
        response = GraphQLResponse(
            data={"user": {"id": "1"}},
            response_time_ms=100
        )
        
        base_client.execute_query = AsyncMock(
            side_effect=[
                GraphQLClientError("Network error"),
                GraphQLClientError("Network error"), 
                response
            ]
        )
        
        result = await retryable_client.execute_with_retry("query { user { id } }")
        
        assert result.data == {"user": {"id": "1"}}
        assert base_client.execute_query.call_count == 3
    
    async def test_max_retries_exceeded(self, retryable_client, base_client):
        """Test behavior when max retries are exceeded."""
        base_client.execute_query = AsyncMock(
            side_effect=GraphQLClientError("Persistent error")
        )
        
        with pytest.raises(GraphQLClientError):
            await retryable_client.execute_with_retry("query { user { id } }")
        
        # Should try initial + 2 retries = 3 total
        assert base_client.execute_query.call_count == 3


@pytest.mark.asyncio
async def test_integration_example():
    """Integration test example showing full client stack."""
    # Create endpoint
    from fraiseql_doctor.models.endpoint import AuthType
    endpoint = Endpoint(
        id=uuid4(),
        name="Integration Test",
        url="https://api.example.com/graphql",
        auth_type=AuthType.BEARER,
        auth_config={"token": "test-token"},
        timeout_seconds=30,
        max_retries=2
    )
    
    # Create session and client
    session = aiohttp.ClientSession()
    base_client = FraiseQLClient(endpoint, session)
    retryable_client = RetryableClient(base_client, endpoint)
    
    # Mock successful response
    with aioresponses() as m:
        m.post(
            str(endpoint.url),
            payload={
                "data": {"users": [{"id": "1", "name": "Test User"}]},
                "extensions": {"complexity": 25}
            }
        )
        
        response = await retryable_client.execute_with_retry(
            "query { users { id name } }"
        )
        
        assert response.data["users"][0]["name"] == "Test User"
        assert response.complexity_score == 25
    
    await session.close()
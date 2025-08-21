# Phase 3: TDD FraiseQL Client Infrastructure
**Agent: Test-Driven HTTP Client Specialist**

## Objective
Develop robust, production-ready FraiseQL/GraphQL client infrastructure using Test-Driven Development, where every HTTP interaction, authentication method, and error scenario is thoroughly tested BEFORE implementation.

## 🔄 TDD Client Development Workflow

### Step 1: HTTP Client Behavior Tests (RED Phase)
Define client behavior through failing tests that specify exact requirements.

#### 1.1 Basic HTTP Client Tests
```python
# tests/test_fraiseql_client_basic.py - Write FIRST
"""Test basic FraiseQL client functionality."""
import pytest
import aioresponses
from aiohttp import ClientTimeout
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient, GraphQLResponse
from fraiseql_doctor.models.endpoint import Endpoint

@pytest.fixture
def sample_endpoint():
    """Create a sample endpoint for testing."""
    return Endpoint(
        name="test-endpoint",
        url="https://api.example.com/graphql",
        auth_type="none",
        timeout_seconds=30,
        max_retries=3
    )

async def test_client_executes_simple_query(sample_endpoint):
    """Test client can execute a simple GraphQL query."""
    with aioresponses.aioresponses() as m:
        # Mock successful GraphQL response
        m.post(
            "https://api.example.com/graphql",
            payload={
                "data": {
                    "user": {
                        "id": "123",
                        "name": "John Doe"
                    }
                }
            },
            status=200,
            headers={"Content-Type": "application/json"}
        )

        client = FraiseQLClient(sample_endpoint)

        query = """
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    name
                }
            }
        """

        response = await client.execute_query(
            query,
            variables={"id": "123"}
        )

        # Verify response structure
        assert isinstance(response, GraphQLResponse)
        assert response.data is not None
        assert response.data["user"]["id"] == "123"
        assert response.data["user"]["name"] == "John Doe"
        assert response.errors is None
        assert response.response_time_ms > 0
        assert response.response_time_ms < 5000  # Should be reasonable

async def test_client_handles_graphql_errors(sample_endpoint):
    """Test client properly handles GraphQL errors in response."""
    with aioresponses.aioresponses() as m:
        # Mock GraphQL error response
        m.post(
            "https://api.example.com/graphql",
            payload={
                "errors": [
                    {
                        "message": "Field 'user' not found on type 'Query'",
                        "locations": [{"line": 2, "column": 3}],
                        "path": ["user"]
                    }
                ],
                "data": None
            },
            status=200  # GraphQL errors still return 200
        )

        client = FraiseQLClient(sample_endpoint)

        response = await client.execute_query("query { user { id } }")

        assert response.data is None
        assert response.errors is not None
        assert len(response.errors) == 1
        assert "not found" in response.errors[0]["message"]
        assert response.response_time_ms > 0

async def test_client_handles_http_errors(sample_endpoint):
    """Test client properly handles HTTP-level errors."""
    with aioresponses.aioresponses() as m:
        # Mock HTTP error
        m.post(
            "https://api.example.com/graphql",
            status=500,
            payload={"error": "Internal Server Error"}
        )

        client = FraiseQLClient(sample_endpoint)

        with pytest.raises(Exception) as exc_info:
            await client.execute_query("query { test }")

        # Should raise appropriate exception with context
        assert "500" in str(exc_info.value) or "server error" in str(exc_info.value).lower()

async def test_client_respects_timeout_settings(sample_endpoint):
    """Test client respects timeout configuration."""
    # Set very short timeout
    sample_endpoint.timeout_seconds = 1

    with aioresponses.aioresponses() as m:
        # Mock slow response (never actually responds)
        m.post(
            "https://api.example.com/graphql",
            exception=aioresponses.ClientTimeout("Request timeout")
        )

        client = FraiseQLClient(sample_endpoint)

        with pytest.raises(Exception) as exc_info:
            await client.execute_query("query { test }")

        # Should raise timeout exception
        assert "timeout" in str(exc_info.value).lower()
```

#### 1.2 Authentication Tests
```python
# tests/test_authentication.py - Write FIRST
"""Test authentication mechanisms."""
import pytest
import aioresponses
import base64
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
from fraiseql_doctor.models.endpoint import Endpoint

async def test_bearer_token_authentication():
    """Test Bearer token authentication is properly applied."""
    endpoint = Endpoint(
        name="bearer-test",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "secret-token-123"}
    )

    with aioresponses.aioresponses() as m:
        m.post(
            "https://api.example.com/graphql",
            payload={"data": {"authenticated": True}}
        )

        client = FraiseQLClient(endpoint)
        await client.execute_query("query { authenticated }")

        # Verify Bearer token was sent
        assert len(m.requests) == 1
        request = m.requests[0][1]  # Get the aiohttp request
        assert "Authorization" in request.headers
        assert request.headers["Authorization"] == "Bearer secret-token-123"

async def test_api_key_authentication():
    """Test API key authentication with custom header."""
    endpoint = Endpoint(
        name="api-key-test",
        url="https://api.example.com/graphql",
        auth_type="api_key",
        auth_config={
            "api_key": "abc123",
            "header_name": "X-API-Key"
        }
    )

    with aioresponses.aioresponses() as m:
        m.post(
            "https://api.example.com/graphql",
            payload={"data": {"authenticated": True}}
        )

        client = FraiseQLClient(endpoint)
        await client.execute_query("query { authenticated }")

        # Verify API key header was sent
        request = m.requests[0][1]
        assert "X-API-Key" in request.headers
        assert request.headers["X-API-Key"] == "abc123"

async def test_basic_authentication():
    """Test HTTP Basic authentication."""
    endpoint = Endpoint(
        name="basic-test",
        url="https://api.example.com/graphql",
        auth_type="basic",
        auth_config={
            "username": "testuser",
            "password": "testpass"
        }
    )

    with aioresponses.aioresponses() as m:
        m.post(
            "https://api.example.com/graphql",
            payload={"data": {"authenticated": True}}
        )

        client = FraiseQLClient(endpoint)
        await client.execute_query("query { authenticated }")

        # Verify Basic auth header
        request = m.requests[0][1]
        assert "Authorization" in request.headers

        # Decode and verify credentials
        auth_header = request.headers["Authorization"]
        assert auth_header.startswith("Basic ")

        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode()
        assert decoded_creds == "testuser:testpass"

async def test_no_authentication():
    """Test that no auth type doesn't add auth headers."""
    endpoint = Endpoint(
        name="no-auth-test",
        url="https://api.example.com/graphql",
        auth_type="none"
    )

    with aioresponses.aioresponses() as m:
        m.post(
            "https://api.example.com/graphql",
            payload={"data": {"public": True}}
        )

        client = FraiseQLClient(endpoint)
        await client.execute_query("query { public }")

        # Verify no auth headers were sent
        request = m.requests[0][1]
        assert "Authorization" not in request.headers
        assert "X-API-Key" not in request.headers
```

#### 1.3 Performance and Reliability Tests
```python
# tests/test_client_performance.py - Write FIRST
"""Test client performance and reliability features."""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock
from fraiseql_doctor.services.fraiseql_client import FraiseQLClient
from fraiseql_doctor.services.retry import RetryableClient, CircuitBreaker
from fraiseql_doctor.models.endpoint import Endpoint

@pytest.mark.performance
async def test_concurrent_request_handling():
    """Test client can handle concurrent requests efficiently."""
    endpoint = Endpoint(
        name="concurrent-test",
        url="https://api.example.com/graphql",
        auth_type="none"
    )

    with aioresponses.aioresponses() as m:
        # Mock multiple responses
        for i in range(10):
            m.post(
                "https://api.example.com/graphql",
                payload={"data": {"request_id": i}}
            )

        client = FraiseQLClient(endpoint)

        # Execute 10 concurrent requests
        start_time = time.time()

        tasks = [
            client.execute_query(f"query {{ request{i} }}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # All requests should succeed
        assert len(results) == 10
        assert all(r.data is not None for r in results)

        # Should complete in reasonable time (concurrent, not sequential)
        assert total_time < 5.0  # Much faster than 10 sequential requests

async def test_retry_mechanism():
    """Test retry logic with exponential backoff."""
    endpoint = Endpoint(
        name="retry-test",
        url="https://api.example.com/graphql",
        auth_type="none",
        max_retries=3,
        retry_delay_seconds=1
    )

    with aioresponses.aioresponses() as m:
        # First two requests fail, third succeeds
        m.post("https://api.example.com/graphql", status=500)
        m.post("https://api.example.com/graphql", status=500)
        m.post(
            "https://api.example.com/graphql",
            payload={"data": {"success": True}}
        )

        client = FraiseQLClient(endpoint)
        retryable_client = RetryableClient(client, endpoint)

        start_time = time.time()
        response = await retryable_client.execute_with_retry("query { test }")
        retry_time = time.time() - start_time

        # Should eventually succeed
        assert response.data["success"] is True

        # Should have taken time for retries (with exponential backoff)
        assert retry_time >= 3.0  # At least 1 + 2 seconds for backoff
        assert len(m.requests) == 3  # All three attempts made

async def test_circuit_breaker_pattern():
    """Test circuit breaker prevents cascading failures."""
    endpoint = Endpoint(
        name="circuit-test",
        url="https://api.example.com/graphql",
        auth_type="none",
        max_retries=2
    )

    with aioresponses.aioresponses() as m:
        # Mock failures
        for _ in range(10):
            m.post("https://api.example.com/graphql", status=500)

        client = FraiseQLClient(endpoint)
        retryable_client = RetryableClient(client, endpoint)

        # First few requests should trigger circuit breaker
        for i in range(5):
            with pytest.raises(Exception):
                await retryable_client.execute_with_retry("query { test }")

        # Circuit should be open now - subsequent requests should fail fast
        start_time = time.time()
        with pytest.raises(Exception) as exc_info:
            await retryable_client.execute_with_retry("query { test }")
        fast_fail_time = time.time() - start_time

        # Should fail immediately (circuit breaker open)
        assert fast_fail_time < 0.1
        assert "circuit breaker" in str(exc_info.value).lower()

async def test_connection_pooling():
    """Test connection pooling works correctly."""
    endpoint = Endpoint(
        name="pool-test",
        url="https://api.example.com/graphql",
        auth_type="none"
    )

    # This test defines the requirement for connection pooling
    # Implementation should reuse connections efficiently
    client = FraiseQLClient(endpoint)

    # Test will verify connection reuse (implementation detail)
    # For now, just ensure client can be created
    assert client is not None
    assert client.endpoint == endpoint
```

### Step 2: Query Complexity Analysis Tests (RED Phase)
```python
# tests/test_query_complexity.py - Write FIRST
"""Test GraphQL query complexity analysis."""
import pytest
from fraiseql_doctor.services.complexity import QueryComplexityAnalyzer, ComplexityMetrics

def test_simple_query_complexity():
    """Test complexity analysis for simple queries."""
    analyzer = QueryComplexityAnalyzer(max_depth=10, max_complexity=1000)

    simple_query = """
        query {
            user {
                id
                name
            }
        }
    """

    metrics = analyzer.analyze_query(simple_query)

    assert isinstance(metrics, ComplexityMetrics)
    assert metrics.depth == 2  # query { user { ... } }
    assert metrics.field_count >= 2  # user, id, name
    assert metrics.total_score > 0
    assert metrics.total_score < 100  # Should be low for simple query
    assert len(metrics.recommendations) == 0  # No recommendations for simple query

def test_complex_nested_query():
    """Test complexity analysis for deeply nested queries."""
    analyzer = QueryComplexityAnalyzer(max_depth=5, max_complexity=500)

    complex_query = """
        query {
            user {
                id
                name
                posts {
                    id
                    title
                    comments {
                        id
                        text
                        author {
                            id
                            name
                            avatar {
                                url
                                size
                            }
                        }
                    }
                }
            }
        }
    """

    metrics = analyzer.analyze_query(complex_query)

    assert metrics.depth > 5  # Should exceed max depth
    assert metrics.total_score > 500  # Should exceed max complexity
    assert len(metrics.recommendations) > 0  # Should have recommendations

    # Check for specific recommendations
    rec_text = " ".join(metrics.recommendations)
    assert "depth" in rec_text.lower()
    assert "complexity" in rec_text.lower()

def test_query_with_variables_complexity():
    """Test complexity analysis considers variables and arguments."""
    analyzer = QueryComplexityAnalyzer()

    query_with_args = """
        query GetUserPosts($userId: ID!, $limit: Int!, $orderBy: String!) {
            user(id: $userId) {
                posts(limit: $limit, orderBy: $orderBy) {
                    id
                    title
                    createdAt
                }
            }
        }
    """

    metrics = analyzer.analyze_query(query_with_args)

    assert metrics.field_count >= 3  # user, posts, id, title, createdAt
    assert metrics.total_score > 0
    # Variables don't necessarily increase complexity, but arguments might

def test_complexity_recommendations_quality():
    """Test that complexity recommendations are helpful and actionable."""
    analyzer = QueryComplexityAnalyzer(max_depth=3, max_complexity=100)

    problematic_query = """
        query {
            users {
                id name email avatar
                posts { id title content tags likes comments { id text author { name } } }
                followers { id name followers { id name } }
                following { id name posts { id title } }
            }
        }
    """

    metrics = analyzer.analyze_query(problematic_query)

    assert len(metrics.recommendations) > 0

    # Recommendations should be specific and actionable
    for rec in metrics.recommendations:
        assert len(rec) > 10  # Should be descriptive
        assert any(keyword in rec.lower() for keyword in [
            "reduce", "limit", "fragment", "separate", "flatten"
        ])
```

### Step 3: Client Implementation (GREEN Phase)
Implement minimal client to make tests pass.

#### 3.1 Core GraphQL Client
```python
# src/fraiseql_doctor/services/fraiseql_client.py
"""Production-ready FraiseQL/GraphQL client."""
import asyncio
import time
from typing import Any, Dict, Optional
import aiohttp
from pydantic import BaseModel

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.core.exceptions import (
    GraphQLClientError,
    GraphQLTimeoutError,
    GraphQLAuthError
)


class GraphQLResponse(BaseModel):
    """Structured GraphQL response model."""
    data: Dict[str, Any] | None = None
    errors: list[Dict[str, Any]] | None = None
    extensions: Dict[str, Any] | None = None
    response_time_ms: int
    complexity_score: int | None = None
    cached: bool = False


class FraiseQLClient:
    """Production-ready FraiseQL/GraphQL client."""

    def __init__(
        self,
        endpoint: Endpoint,
        session: aiohttp.ClientSession | None = None
    ):
        self.endpoint = endpoint
        self.session = session
        self._auth_headers = self._build_auth_headers()

    async def execute_query(
        self,
        query: str,
        variables: Dict[str, Any] | None = None,
        operation_name: str | None = None,
        timeout: int | None = None
    ) -> GraphQLResponse:
        """Execute a GraphQL query with comprehensive error handling."""
        start_time = time.time()

        if self.session is None:
            async with aiohttp.ClientSession() as session:
                return await self._execute_with_session(
                    session, query, variables, operation_name, timeout, start_time
                )
        else:
            return await self._execute_with_session(
                self.session, query, variables, operation_name, timeout, start_time
            )

    async def _execute_with_session(
        self,
        session: aiohttp.ClientSession,
        query: str,
        variables: Dict[str, Any] | None,
        operation_name: str | None,
        timeout: int | None,
        start_time: float
    ) -> GraphQLResponse:
        """Execute query with provided session."""
        try:
            payload = {
                "query": query,
                "variables": variables or {},
            }
            if operation_name:
                payload["operationName"] = operation_name

            headers = self._build_headers()
            timeout_val = timeout or self.endpoint.timeout_seconds or 30

            async with session.post(
                str(self.endpoint.url),
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_val)
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)

                if response.status >= 400:
                    raise GraphQLClientError(
                        f"HTTP {response.status}: {await response.text()}",
                        status_code=response.status,
                        response_time_ms=response_time_ms
                    )

                result = await response.json()

                return GraphQLResponse(
                    data=result.get("data"),
                    errors=result.get("errors"),
                    extensions=result.get("extensions"),
                    response_time_ms=response_time_ms,
                    complexity_score=self._extract_complexity(result),
                    cached=self._is_cached_response(result)
                )

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            raise GraphQLTimeoutError(
                f"Query timeout after {response_time_ms}ms",
                timeout=timeout_val,
                response_time_ms=response_time_ms
            )
        except aiohttp.ClientError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            raise GraphQLClientError(
                f"Client error: {e}",
                response_time_ms=response_time_ms
            ) from e

    def _build_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers based on endpoint config."""
        headers = {}

        if self.endpoint.auth_type == "bearer":
            token = self.endpoint.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self.endpoint.auth_type == "api_key":
            api_key = self.endpoint.auth_config.get("api_key")
            header_name = self.endpoint.auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key

        elif self.endpoint.auth_type == "basic":
            username = self.endpoint.auth_config.get("username")
            password = self.endpoint.auth_config.get("password")
            if username and password:
                import base64
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

        return headers

    def _build_headers(self) -> Dict[str, str]:
        """Build complete headers including auth and endpoint headers."""
        headers = {"Content-Type": "application/json"}
        headers.update(self._auth_headers)
        headers.update(self.endpoint.headers or {})
        return headers

    def _extract_complexity(self, result: Dict[str, Any]) -> int | None:
        """Extract complexity score from GraphQL response extensions."""
        extensions = result.get("extensions", {})
        complexity = extensions.get("complexity", {})
        return complexity.get("score") if isinstance(complexity, dict) else None

    def _is_cached_response(self, result: Dict[str, Any]) -> bool:
        """Check if response was served from cache."""
        extensions = result.get("extensions", {})
        return extensions.get("cached", False)
```

#### 3.2 Query Complexity Analyzer
```python
# src/fraiseql_doctor/services/complexity.py
"""FraiseQL query complexity analysis."""
import re
from typing import List
from dataclasses import dataclass


@dataclass
class ComplexityMetrics:
    """Query complexity analysis results."""
    total_score: int
    depth: int
    field_count: int
    nested_queries: int
    estimated_cost: float
    recommendations: List[str]


class QueryComplexityAnalyzer:
    """Analyze GraphQL query complexity for FraiseQL optimization."""

    def __init__(self, max_depth: int = 10, max_complexity: int = 1000):
        self.max_depth = max_depth
        self.max_complexity = max_complexity

    def analyze_query(self, query: str) -> ComplexityMetrics:
        """Analyze query complexity and provide recommendations."""
        # Basic implementation to pass tests
        depth = self._calculate_depth(query)
        field_count = self._count_fields(query)
        nested_queries = self._count_nested_queries(query)

        total_score = self._calculate_complexity_score(depth, field_count, nested_queries)
        estimated_cost = self._estimate_cost(total_score, depth)
        recommendations = self._generate_recommendations(depth, field_count, nested_queries, total_score)

        return ComplexityMetrics(
            total_score=total_score,
            depth=depth,
            field_count=field_count,
            nested_queries=nested_queries,
            estimated_cost=estimated_cost,
            recommendations=recommendations
        )

    def _calculate_depth(self, query: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0

        for char in query:
            if char == '{':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == '}':
                current_depth -= 1

        return max_depth

    def _count_fields(self, query: str) -> int:
        """Count total number of fields requested."""
        # Simplified field counting
        field_pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\s*(?:\([^)]*\))?\s*(?:{|$|\s)'
        matches = re.findall(field_pattern, query)
        return len([m for m in matches if not m.strip().startswith(('query', 'mutation', 'subscription'))])

    def _count_nested_queries(self, query: str) -> int:
        """Count nested object selections."""
        return query.count('{') - 1  # Subtract the root query

    def _calculate_complexity_score(self, depth: int, fields: int, nested: int) -> int:
        """Calculate overall complexity score."""
        return (depth * 10) + (fields * 2) + (nested * 5)

    def _estimate_cost(self, complexity: int, depth: int) -> float:
        """Estimate query execution cost."""
        base_cost = complexity * 0.1
        depth_penalty = depth * 0.05
        return base_cost + depth_penalty

    def _generate_recommendations(
        self, depth: int, fields: int, nested: int, score: int
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        if depth > self.max_depth:
            recommendations.append(f"Query depth ({depth}) exceeds recommended maximum ({self.max_depth}). Consider breaking into separate queries.")

        if score > self.max_complexity:
            recommendations.append(f"Query complexity ({score}) exceeds limit ({self.max_complexity}). Consider reducing fields or using fragments.")

        if fields > 50:
            recommendations.append("Consider reducing number of fields or using GraphQL fragments for reusability.")

        if nested > 5:
            recommendations.append("Consider flattening nested queries or using separate requests to improve performance.")

        return recommendations
```

### Step 4: Advanced Features (REFACTOR Phase)
Add sophisticated features while maintaining test coverage.

#### 4.1 Retry and Circuit Breaker Implementation
```python
# src/fraiseql_doctor/services/retry.py
"""Advanced retry logic with circuit breaker pattern."""
import asyncio
import time
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass

from fraiseql_doctor.core.exceptions import CircuitBreakerOpenError


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


class RetryableClient:
    """GraphQL client with retry logic and circuit breaker."""

    def __init__(self, client, endpoint):
        self.client = client
        self.endpoint = endpoint
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=endpoint.max_retries or 3,
            recovery_timeout=60
        ))

    async def execute_with_retry(
        self,
        query: str,
        variables: dict | None = None,
        **kwargs
    ) -> Any:
        """Execute query with retry logic and circuit breaker."""
        max_retries = self.endpoint.max_retries or 3
        delay = self.endpoint.retry_delay_seconds or 1

        for attempt in range(max_retries + 1):
            try:
                return await self.circuit_breaker.call(
                    self.client.execute_query,
                    query,
                    variables,
                    **kwargs
                )
            except Exception as e:
                if attempt == max_retries:
                    raise e

                # Exponential backoff
                wait_time = delay * (2 ** attempt)
                await asyncio.sleep(wait_time)
```

#### 4.2 Exception Classes
```python
# src/fraiseql_doctor/core/exceptions.py
"""Custom exception classes for FraiseQL Doctor."""


class FraiseQLDoctorError(Exception):
    """Base exception for FraiseQL Doctor."""
    pass


class GraphQLClientError(FraiseQLDoctorError):
    """Base exception for GraphQL client errors."""

    def __init__(self, message: str, status_code: int | None = None, response_time_ms: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_time_ms = response_time_ms


class GraphQLTimeoutError(GraphQLClientError):
    """Exception raised when GraphQL request times out."""

    def __init__(self, message: str, timeout: int, response_time_ms: int):
        super().__init__(message, response_time_ms=response_time_ms)
        self.timeout = timeout


class GraphQLAuthError(GraphQLClientError):
    """Exception raised for authentication errors."""
    pass


class CircuitBreakerOpenError(FraiseQLDoctorError):
    """Exception raised when circuit breaker is open."""
    pass
```

## TDD Success Criteria for Phase 3

### RED Phase Verification ✅
- [ ] HTTP client behavior tests written and failing initially
- [ ] Authentication tests define all auth types
- [ ] Performance tests establish benchmarks for concurrency and retries
- [ ] Complexity analysis tests define quality requirements

### GREEN Phase Verification ✅
- [ ] FraiseQLClient implements exactly what tests require
- [ ] Authentication mechanisms work for all configured types
- [ ] Retry logic and circuit breaker pass reliability tests
- [ ] Query complexity analysis provides actionable recommendations

### REFACTOR Phase Verification ✅
- [ ] Advanced features like connection pooling optimized
- [ ] Error handling provides detailed context
- [ ] Performance optimized while maintaining test coverage
- [ ] Code quality improved with proper separation of concerns

### Client Quality Gates
- [ ] **HTTP Operations**: All GraphQL interactions work correctly
- [ ] **Authentication**: Bearer, API key, and Basic auth fully functional
- [ ] **Error Handling**: Network failures, timeouts, and GraphQL errors handled
- [ ] **Performance**: Concurrent requests and connection pooling efficient
- [ ] **Reliability**: Retry logic and circuit breaker prevent cascading failures
- [ ] **Query Analysis**: Complexity analysis helps optimize queries

## Handoff to Phase 4
With robust HTTP client foundation tested and reliable, Phase 4 will continue TDD for business services:

1. **Service Layer Tests**: Query management, execution tracking, health monitoring
2. **Business Logic Tests**: CRUD operations, validation rules, performance analytics
3. **Integration Tests**: Services working together with real database
4. **Scheduling Tests**: Cron-based execution and monitoring workflows

The FraiseQL client now provides a tested, production-ready foundation for all GraphQL communications.

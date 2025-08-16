# Phase 3: FraiseQL Client Infrastructure
**Agent: FraiseQL Specialist**

## Objective
Implement robust, production-ready FraiseQL/GraphQL client infrastructure optimized for health monitoring, query execution, and performance analysis across multiple endpoints.

## Requirements

### Core Client Architecture

#### 1. Base GraphQL Client
```python
"""Base GraphQL client with FraiseQL optimizations."""
import asyncio
import json
import time
from typing import Any, Dict, Optional
from uuid import UUID

import aiohttp
from pydantic import BaseModel, HttpUrl

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.core.exceptions import (
    GraphQLClientError,
    GraphQLTimeoutError,
    GraphQLAuthError,
    GraphQLComplexityError
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
        session: aiohttp.ClientSession | None = None,
        default_timeout: int = 30
    ):
        self.endpoint = endpoint
        self.session = session or aiohttp.ClientSession()
        self.default_timeout = default_timeout
        self._auth_headers: Dict[str, str] = {}
        self._setup_authentication()
    
    async def execute_query(
        self,
        query: str,
        variables: Dict[str, Any] | None = None,
        operation_name: str | None = None,
        timeout: int | None = None
    ) -> GraphQLResponse:
        """Execute a GraphQL query with comprehensive error handling."""
        start_time = time.time()
        
        try:
            payload = {
                "query": query,
                "variables": variables or {},
            }
            if operation_name:
                payload["operationName"] = operation_name
            
            headers = self._build_headers()
            timeout_val = timeout or self.endpoint.timeout_seconds or self.default_timeout
            
            async with self.session.post(
                str(self.endpoint.url),
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_val)
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status >= 400:
                    await self._handle_http_error(response, response_time_ms)
                
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
```

#### 2. Authentication Manager
```python
"""Authentication handling for various auth types."""
from abc import ABC, abstractmethod
from typing import Dict, Any
import base64
from datetime import datetime, timedelta

from fraiseql_doctor.models.endpoint import Endpoint


class AuthProvider(ABC):
    """Abstract base for authentication providers."""
    
    @abstractmethod
    async def get_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        pass
    
    @abstractmethod
    async def is_valid(self) -> bool:
        """Check if authentication is still valid."""
        pass


class BearerTokenAuth(AuthProvider):
    """Bearer token authentication."""
    
    def __init__(self, token: str, expires_at: datetime | None = None):
        self.token = token
        self.expires_at = expires_at
    
    async def get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}
    
    async def is_valid(self) -> bool:
        if self.expires_at:
            return datetime.utcnow() < self.expires_at
        return True


class APIKeyAuth(AuthProvider):
    """API key authentication."""
    
    def __init__(self, api_key: str, header_name: str = "X-API-Key"):
        self.api_key = api_key
        self.header_name = header_name
    
    async def get_headers(self) -> Dict[str, str]:
        return {self.header_name: self.api_key}
    
    async def is_valid(self) -> bool:
        return True


class BasicAuth(AuthProvider):
    """Basic authentication."""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    async def get_headers(self) -> Dict[str, str]:
        credentials = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}
    
    async def is_valid(self) -> bool:
        return True


def create_auth_provider(endpoint: Endpoint) -> AuthProvider | None:
    """Factory function to create appropriate auth provider."""
    auth_config = endpoint.auth_config or {}
    
    match endpoint.auth_type:
        case "bearer":
            return BearerTokenAuth(
                token=auth_config["token"],
                expires_at=auth_config.get("expires_at")
            )
        case "api_key":
            return APIKeyAuth(
                api_key=auth_config["api_key"],
                header_name=auth_config.get("header_name", "X-API-Key")
            )
        case "basic":
            return BasicAuth(
                username=auth_config["username"],
                password=auth_config["password"]
            )
        case "none" | _:
            return None
```

#### 3. Query Complexity Analyzer
```python
"""FraiseQL query complexity analysis."""
import re
from typing import Dict, Any, List
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
        # Parse query structure
        depth = self._calculate_depth(query)
        field_count = self._count_fields(query)
        nested_queries = self._count_nested_queries(query)
        
        # Calculate complexity score
        total_score = self._calculate_complexity_score(depth, field_count, nested_queries)
        estimated_cost = self._estimate_cost(total_score, depth)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            depth, field_count, nested_queries, total_score
        )
        
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
        # Simplified field counting - could be enhanced with proper AST parsing
        field_pattern = r'\b\w+\s*(?:\([^)]*\))?\s*(?:{|$)'
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
            recommendations.append(f"Query depth ({depth}) exceeds recommended maximum ({self.max_depth})")
        
        if score > self.max_complexity:
            recommendations.append(f"Query complexity ({score}) exceeds limit ({self.max_complexity})")
        
        if fields > 50:
            recommendations.append("Consider reducing number of fields or using fragments")
        
        if nested > 5:
            recommendations.append("Consider flattening nested queries or using separate requests")
        
        return recommendations
```

#### 4. Connection Pool Manager
```python
"""Connection pool management for multiple endpoints."""
import asyncio
from typing import Dict, Optional
from uuid import UUID

import aiohttp

from fraiseql_doctor.models.endpoint import Endpoint


class ConnectionPoolManager:
    """Manage connection pools for multiple FraiseQL endpoints."""
    
    def __init__(self, max_connections_per_endpoint: int = 10):
        self._pools: Dict[UUID, aiohttp.ClientSession] = {}
        self._max_connections = max_connections_per_endpoint
        self._lock = asyncio.Lock()
    
    async def get_session(self, endpoint: Endpoint) -> aiohttp.ClientSession:
        """Get or create a session for the endpoint."""
        async with self._lock:
            if endpoint.pk_endpoint not in self._pools:
                connector = aiohttp.TCPConnector(
                    limit=self._max_connections,
                    limit_per_host=self._max_connections,
                    ttl_dns_cache=300,
                    use_dns_cache=True,
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=endpoint.timeout_seconds or 30,
                    connect=10
                )
                
                self._pools[endpoint.pk_endpoint] = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=endpoint.headers or {}
                )
            
            return self._pools[endpoint.pk_endpoint]
    
    async def close_session(self, endpoint_id: UUID) -> None:
        """Close session for specific endpoint."""
        async with self._lock:
            if endpoint_id in self._pools:
                await self._pools[endpoint_id].close()
                del self._pools[endpoint_id]
    
    async def close_all(self) -> None:
        """Close all sessions."""
        async with self._lock:
            for session in self._pools.values():
                await session.close()
            self._pools.clear()
```

#### 5. Retry Logic with Circuit Breaker
```python
"""Advanced retry logic with circuit breaker pattern."""
import asyncio
import time
from enum import Enum
from typing import Callable, Any
from dataclasses import dataclass, field

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
    
    def __init__(self, client: FraiseQLClient, endpoint: Endpoint):
        self.client = client
        self.endpoint = endpoint
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=endpoint.max_retries or 3,
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

### Performance Monitoring

#### 6. Metrics Collection
```python
"""Performance metrics collection for FraiseQL queries."""
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from statistics import mean, median

@dataclass
class QueryMetrics:
    """Individual query execution metrics."""
    query_id: str
    endpoint_id: str
    execution_time_ms: int
    response_size_bytes: int
    complexity_score: int | None
    success: bool
    error_message: str | None = None
    timestamp: float = field(default_factory=time.time)


class MetricsCollector:
    """Collect and analyze performance metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.metrics: List[QueryMetrics] = []
        self.max_metrics = max_metrics
    
    def record_query(self, metrics: QueryMetrics) -> None:
        """Record query execution metrics."""
        self.metrics.append(metrics)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]
    
    def get_performance_summary(
        self, 
        endpoint_id: str | None = None,
        time_window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Get performance summary for time window."""
        cutoff_time = time.time() - time_window_seconds
        
        filtered_metrics = [
            m for m in self.metrics 
            if m.timestamp >= cutoff_time and (
                endpoint_id is None or m.endpoint_id == endpoint_id
            )
        ]
        
        if not filtered_metrics:
            return {"error": "No metrics found for criteria"}
        
        successful_metrics = [m for m in filtered_metrics if m.success]
        failed_metrics = [m for m in filtered_metrics if not m.success]
        
        response_times = [m.execution_time_ms for m in successful_metrics]
        
        return {
            "total_queries": len(filtered_metrics),
            "successful_queries": len(successful_metrics),
            "failed_queries": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics) * 100,
            "avg_response_time_ms": mean(response_times) if response_times else 0,
            "median_response_time_ms": median(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
        }
```

### Success Criteria
- [x] Production-ready GraphQL client with error handling
- [x] Multiple authentication methods supported
- [x] Query complexity analysis and optimization
- [x] Connection pooling for multiple endpoints
- [x] Retry logic with circuit breaker pattern
- [x] Comprehensive performance metrics collection
- [x] FraiseQL-specific optimizations implemented
- [x] Async/await patterns throughout

### Handoff Notes for Next Phase
- Use FraiseQLClient as base for all query operations
- Implement proper error handling in business logic
- Use MetricsCollector for performance tracking
- Consider implementing query caching for repeated queries
- Add proper logging for all client operations
- Ensure all database operations store execution metrics
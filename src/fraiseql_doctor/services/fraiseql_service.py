"""High-level FraiseQL service orchestrating all client components."""
import asyncio
from typing import Dict, Any, List, Optional
from uuid import UUID

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.core.database import DatabaseManager
from fraiseql_doctor.core.exceptions import EndpointNotFoundError, GraphQLClientError
from fraiseql_doctor.services.client import FraiseQLClient, GraphQLResponse
from fraiseql_doctor.services.auth import create_auth_provider
from fraiseql_doctor.services.complexity import QueryComplexityAnalyzer
from fraiseql_doctor.services.pool import ConnectionPoolManager
from fraiseql_doctor.services.retry import RetryableClient
from fraiseql_doctor.services.metrics import MetricsCollector, QueryMetrics


class FraiseQLService:
    """High-level service for FraiseQL operations with full monitoring."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.pool_manager = ConnectionPoolManager()
        self.metrics_collector = MetricsCollector()
        self.complexity_analyzer = QueryComplexityAnalyzer()
        self._clients: Dict[UUID, RetryableClient] = {}
    
    async def execute_query(
        self,
        endpoint_id: UUID,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        validate_complexity: bool = True,
        **kwargs
    ) -> GraphQLResponse:
        """Execute a query against a specific endpoint with full monitoring."""
        # Get endpoint from database
        endpoint = await self._get_endpoint(endpoint_id)
        
        # Validate query complexity if requested
        if validate_complexity:
            complexity_validation = self.complexity_analyzer.validate_query_limits(query)
            if not complexity_validation["valid"]:
                raise GraphQLClientError(
                    f"Query complexity validation failed: {complexity_validation['violations']}"
                )
        
        # Get or create client for endpoint
        client = await self._get_client(endpoint)
        
        # Generate query ID for tracking
        query_id = self._generate_query_id(query, variables, operation_name)
        
        # Execute query and collect metrics
        start_time = asyncio.get_event_loop().time()
        error_message = None
        error_type = None
        success = False
        
        try:
            response = await client.execute_with_retry(
                query, variables, operation_name=operation_name, **kwargs
            )
            success = response.errors is None or len(response.errors) == 0
            
            if not success and response.errors:
                error_message = "; ".join([err.get("message", "") for err in response.errors])
                error_type = "graphql_error"
            
            return response
            
        except Exception as e:
            error_message = str(e)
            error_type = type(e).__name__
            raise
            
        finally:
            # Record metrics
            execution_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            # Calculate response size (approximate)
            response_size = 0
            if 'response' in locals():
                response_size = len(str(response.data or "")) + len(str(response.errors or ""))
            
            metrics = QueryMetrics(
                query_id=query_id,
                endpoint_id=str(endpoint_id),
                operation_name=operation_name,
                execution_time_ms=execution_time_ms,
                response_size_bytes=response_size,
                complexity_score=getattr(response, 'complexity_score', None) if 'response' in locals() else None,
                success=success,
                error_message=error_message,
                error_type=error_type,
                cached=getattr(response, 'cached', False) if 'response' in locals() else False
            )
            
            self.metrics_collector.record_query(metrics)
    
    async def introspect_endpoint(self, endpoint_id: UUID) -> Dict[str, Any]:
        """Perform schema introspection on an endpoint."""
        endpoint = await self._get_endpoint(endpoint_id)
        client = await self._get_client(endpoint)
        
        # Use the base client for introspection (no retry logic needed)
        return await client.client.introspect_schema()
    
    async def health_check_endpoint(self, endpoint_id: UUID) -> Dict[str, Any]:
        """Perform health check on a specific endpoint."""
        try:
            endpoint = await self._get_endpoint(endpoint_id)
            client = await self._get_client(endpoint)
            
            result = await client.health_check_with_retry()
            
            # Add endpoint info to result
            result.update({
                "endpoint_id": str(endpoint_id),
                "endpoint_url": str(endpoint.url),
                "endpoint_name": endpoint.name
            })
            
            return result
            
        except Exception as e:
            return {
                "endpoint_id": str(endpoint_id),
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def health_check_all_endpoints(self) -> Dict[str, Any]:
        """Perform health check on all configured endpoints."""
        # Get all endpoints from database
        async with self.db.get_async_session() as session:
            from sqlalchemy import select
            from fraiseql_doctor.models.endpoint import Endpoint
            
            stmt = select(Endpoint.id).where(Endpoint.is_active == True)
            result = await session.execute(stmt)
            endpoint_ids = [row[0] for row in result.fetchall()]
        
        # Perform health checks concurrently
        tasks = [
            self.health_check_endpoint(endpoint_id) 
            for endpoint_id in endpoint_ids
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        healthy_count = 0
        total_count = len(results)
        endpoint_results = []
        
        for result in results:
            if isinstance(result, Exception):
                endpoint_results.append({
                    "healthy": False,
                    "error": str(result),
                    "error_type": type(result).__name__
                })
            else:
                endpoint_results.append(result)
                if result.get("healthy", False):
                    healthy_count += 1
        
        return {
            "overall_healthy": healthy_count == total_count,
            "healthy_endpoints": healthy_count,
            "total_endpoints": total_count,
            "health_rate": (healthy_count / total_count * 100) if total_count > 0 else 0,
            "endpoints": endpoint_results
        }
    
    async def get_performance_metrics(
        self,
        endpoint_id: Optional[UUID] = None,
        time_window_seconds: int = 3600
    ) -> Dict[str, Any]:
        """Get performance metrics for endpoints."""
        endpoint_id_str = str(endpoint_id) if endpoint_id else None
        return self.metrics_collector.get_performance_summary(
            endpoint_id_str, time_window_seconds
        )
    
    async def get_endpoint_comparison(self, time_window_seconds: int = 3600) -> Dict[str, Any]:
        """Compare performance across all endpoints."""
        return self.metrics_collector.get_endpoint_comparison(time_window_seconds)
    
    async def get_slow_queries(
        self,
        threshold_ms: int = 1000,
        limit: int = 10,
        time_window_seconds: int = 3600
    ) -> List[Dict[str, Any]]:
        """Get slowest queries above threshold."""
        return self.metrics_collector.get_slow_queries(
            threshold_ms, limit, time_window_seconds
        )
    
    async def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """Analyze query complexity and get optimization recommendations."""
        metrics = self.complexity_analyzer.analyze_query(query)
        validation = self.complexity_analyzer.validate_query_limits(query)
        
        return {
            "complexity_metrics": {
                "total_score": metrics.total_score,
                "depth": metrics.depth,
                "field_count": metrics.field_count,
                "nested_queries": metrics.nested_queries,
                "estimated_cost": metrics.estimated_cost,
                "recommendations": metrics.recommendations
            },
            "validation": validation
        }
    
    async def get_circuit_breaker_stats(self, endpoint_id: UUID) -> Dict[str, Any]:
        """Get circuit breaker statistics for an endpoint."""
        if endpoint_id not in self._clients:
            return {"error": "No client found for endpoint"}
        
        client = self._clients[endpoint_id]
        return client.get_circuit_breaker_stats()
    
    async def reset_circuit_breaker(self, endpoint_id: UUID) -> Dict[str, Any]:
        """Reset circuit breaker for an endpoint."""
        if endpoint_id not in self._clients:
            return {"error": "No client found for endpoint"}
        
        client = self._clients[endpoint_id]
        client.reset_circuit_breaker()
        return {"success": True, "message": "Circuit breaker reset"}
    
    async def _get_endpoint(self, endpoint_id: UUID) -> Endpoint:
        """Get endpoint from database."""
        async with self.db.get_async_session() as session:
            from sqlalchemy import text, select
            from fraiseql_doctor.models.endpoint import Endpoint
            
            # Use ORM instead of raw SQL for better type safety
            stmt = select(Endpoint).where(Endpoint.id == endpoint_id)
            result = await session.execute(stmt)
            endpoint = result.scalar_one_or_none()
            
            if not endpoint:
                raise EndpointNotFoundError(f"Endpoint {endpoint_id} not found")
            
            return endpoint
    
    async def _get_client(self, endpoint: Endpoint) -> RetryableClient:
        """Get or create a retryable client for the endpoint."""
        if endpoint.id not in self._clients:
            # Get session from pool manager
            session = await self.pool_manager.get_session(endpoint)
            
            # Create base client
            base_client = FraiseQLClient(endpoint, session)
            
            # Wrap with retry logic
            retryable_client = RetryableClient(base_client, endpoint)
            
            self._clients[endpoint.id] = retryable_client
        
        return self._clients[endpoint.id]
    
    def _generate_query_id(
        self, 
        query: str, 
        variables: Optional[Dict[str, Any]], 
        operation_name: Optional[str]
    ) -> str:
        """Generate a unique ID for query tracking."""
        import hashlib
        
        content = query
        if variables:
            content += str(sorted(variables.items()))
        if operation_name:
            content += operation_name
        
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        # Close all client connections
        for client in self._clients.values():
            await client.client.close()
        
        # Close pool manager
        await self.pool_manager.close_all()
        
        # Clear caches
        self._clients.clear()
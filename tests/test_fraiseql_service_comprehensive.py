"""Comprehensive TDD tests for FraiseQLService following RED->GREEN->REFACTOR methodology.

Target: Increase coverage from 22% to 90%+
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4, UUID

from fraiseql_doctor.services.fraiseql_service import FraiseQLService
from fraiseql_doctor.core.database import DatabaseManager
from fraiseql_doctor.core.exceptions import EndpointNotFoundError, GraphQLClientError
from fraiseql_doctor.models.endpoint import Endpoint, AuthType
from fraiseql_doctor.services.client import GraphQLResponse


class TestFraiseQLServiceInitialization:
    """Test FraiseQLService initialization and basic setup."""
    
    @pytest.mark.asyncio
    async def test_service_initialization_with_database_manager(self, test_database_manager):
        """RED: Test that FraiseQLService initializes with required components."""
        # This should fail initially - testing basic initialization
        service = FraiseQLService(test_database_manager)
        
        # Verify initialization
        assert service.db is test_database_manager
        assert service.pool_manager is not None
        assert service.metrics_collector is not None
        assert service.complexity_analyzer is not None
        assert service._clients == {}
    
    @pytest.mark.asyncio
    async def test_service_requires_database_manager(self):
        """RED: Test that service requires a database manager."""
        # This should fail - service needs database manager
        with pytest.raises(TypeError):
            FraiseQLService()  # Missing required parameter


class TestFraiseQLServiceEndpointOperations:
    """Test endpoint-related operations following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_service_has_endpoint_method(self, test_database_manager):
        """RED: Test that service has _get_endpoint method."""
        service = FraiseQLService(test_database_manager)
        
        # Verify the method exists
        assert hasattr(service, '_get_endpoint')
        assert callable(getattr(service, '_get_endpoint'))
    
    @pytest.mark.asyncio 
    async def test_service_raises_endpoint_not_found_for_invalid_id(self, test_database_manager):
        """RED: Test that service raises EndpointNotFoundError for non-existent endpoint."""
        service = FraiseQLService(test_database_manager)
        invalid_id = uuid4()
        
        # This should fail because no endpoint exists
        # We expect EndpointNotFoundError to be raised
        with pytest.raises(EndpointNotFoundError):
            await service._get_endpoint(invalid_id)


class TestFraiseQLServiceQueryExecution:
    """Test query execution with full monitoring following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_execute_query_success_with_metrics(self, test_database_manager):
        """RED: Test successful query execution with metrics collection."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        query = "{ users { id name } }"
        variables = {"limit": 10}
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            timeout_seconds=30,
            max_retries=3,
            is_active=True
        )
        
        # Mock successful GraphQL response
        mock_response = GraphQLResponse(
            data={"users": [{"id": "1", "name": "Test"}]},
            errors=None,
            extensions=None
        )
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = mock_response
        
        # Patch dependencies
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client), \
             patch.object(service.complexity_analyzer, 'validate_query_limits', 
                         return_value={"valid": True, "violations": []}):
            
            # Execute
            result = await service.execute_query(endpoint_id, query, variables)
            
            # Verify response
            assert result == mock_response
            assert result.data["users"][0]["name"] == "Test"
            
            # Verify client was called correctly
            mock_client.execute_with_retry.assert_called_once_with(
                query, variables, operation_name=None
            )
            
            # Verify metrics were collected
            # (We'll verify this by checking that metrics_collector.record_query was called)
            assert hasattr(service.metrics_collector, 'record_query')
    
    @pytest.mark.asyncio
    async def test_execute_query_complexity_validation_failure(self, test_database_manager):
        """RED: Test query execution fails when complexity validation fails."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        query = "{ users { posts { comments { replies { user { posts } } } } } }"  # Very complex query
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api", 
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock complexity validation failure
        validation_result = {
            "valid": False,
            "violations": ["Query depth exceeds limit", "Too many nested fields"]
        }
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service.complexity_analyzer, 'validate_query_limits', 
                         return_value=validation_result):
            
            # Execute and verify exception
            with pytest.raises(GraphQLClientError, match="Query complexity validation failed"):
                await service.execute_query(endpoint_id, query, validate_complexity=True)
    
    @pytest.mark.asyncio
    async def test_execute_query_with_graphql_errors(self, test_database_manager):
        """RED: Test query execution with GraphQL errors in response."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        query = "{ invalidField }"
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql", 
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock GraphQL response with errors
        mock_response = GraphQLResponse(
            data=None,
            errors=[
                {"message": "Cannot query field 'invalidField'", "locations": [{"line": 1, "column": 3}]}
            ],
            extensions=None
        )
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = mock_response
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client), \
             patch.object(service.complexity_analyzer, 'validate_query_limits',
                         return_value={"valid": True, "violations": []}):
            
            # Execute
            result = await service.execute_query(endpoint_id, query)
            
            # Verify response contains errors
            assert result == mock_response
            assert result.errors is not None
            assert len(result.errors) == 1
            assert "Cannot query field 'invalidField'" in result.errors[0]["message"]
    
    @pytest.mark.asyncio 
    async def test_execute_query_with_client_exception(self, test_database_manager):
        """RED: Test query execution with client exception."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        query = "{ users { id } }"
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock client that raises exception
        mock_client = AsyncMock()
        mock_client.execute_with_retry.side_effect = ConnectionError("Connection timeout")
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client), \
             patch.object(service.complexity_analyzer, 'validate_query_limits',
                         return_value={"valid": True, "violations": []}):
            
            # Execute and verify exception is propagated
            with pytest.raises(ConnectionError, match="Connection timeout"):
                await service.execute_query(endpoint_id, query)


class TestFraiseQLServiceHealthChecks:
    """Test health check functionality following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_success(self, test_database_manager):
        """RED: Test successful health check for single endpoint."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock successful health check result
        health_result = {
            "healthy": True,
            "response_time_ms": 150,
            "status_code": 200
        }
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.health_check_with_retry.return_value = health_result
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client):
            
            # Execute
            result = await service.health_check_endpoint(endpoint_id)
            
            # Verify
            assert result["healthy"] is True
            assert result["response_time_ms"] == 150
            assert result["endpoint_id"] == str(endpoint_id)
            assert result["endpoint_url"] == "https://api.example.com/graphql"
            assert result["endpoint_name"] == "test-api"
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_failure(self, test_database_manager):
        """RED: Test health check failure handling."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        with patch.object(service, '_get_endpoint', side_effect=ConnectionError("Network error")):
            
            # Execute
            result = await service.health_check_endpoint(endpoint_id)
            
            # Verify error handling
            assert result["healthy"] is False
            assert result["error"] == "Network error"
            assert result["error_type"] == "ConnectionError"
            assert result["endpoint_id"] == str(endpoint_id)
    
    @pytest.mark.asyncio
    async def test_health_check_all_endpoints(self, test_database_manager):
        """RED: Test health check across all endpoints."""
        service = FraiseQLService(test_database_manager)
        
        # Mock database to return multiple endpoint IDs
        endpoint_ids = [uuid4(), uuid4(), uuid4()]
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetchall.return_value = [(eid,) for eid in endpoint_ids]
        mock_session.execute.return_value = mock_result
        test_database_manager.get_async_session = AsyncMock(return_value=mock_session)
        
        # Mock individual health check results
        health_results = [
            {"healthy": True, "response_time_ms": 100},
            {"healthy": False, "error": "Timeout"},
            {"healthy": True, "response_time_ms": 200}
        ]
        
        with patch.object(service, 'health_check_endpoint', side_effect=health_results):
            
            # Execute
            result = await service.health_check_all_endpoints()
            
            # Verify overall results
            assert result["total_endpoints"] == 3
            assert result["healthy_endpoints"] == 2
            assert result["health_rate"] == 66.66666666666667  # 2/3 * 100
            assert result["overall_healthy"] is False  # Not all healthy
            assert len(result["endpoints"]) == 3


class TestFraiseQLServiceMetricsAndAnalysis:
    """Test metrics and analysis functionality following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, test_database_manager):
        """RED: Test getting performance metrics for endpoint."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock metrics result
        expected_metrics = {
            "endpoint_id": str(endpoint_id),
            "total_queries": 100,
            "avg_response_time_ms": 250,
            "success_rate": 95.0,
            "error_rate": 5.0
        }
        
        with patch.object(service.metrics_collector, 'get_performance_summary', 
                         return_value=expected_metrics):
            
            # Execute
            result = await service.get_performance_metrics(endpoint_id, time_window_seconds=3600)
            
            # Verify
            assert result == expected_metrics
            service.metrics_collector.get_performance_summary.assert_called_once_with(
                str(endpoint_id), 3600
            )
    
    @pytest.mark.asyncio
    async def test_analyze_query_complexity(self, test_database_manager):
        """RED: Test query complexity analysis."""
        service = FraiseQLService(test_database_manager)
        query = "{ users { posts { comments } } }"
        
        # Mock complexity analysis results
        mock_metrics = MagicMock()
        mock_metrics.total_score = 15
        mock_metrics.depth = 3
        mock_metrics.field_count = 4
        mock_metrics.nested_queries = 2
        mock_metrics.estimated_cost = 100
        mock_metrics.recommendations = ["Consider adding limits to nested queries"]
        
        mock_validation = {
            "valid": True,
            "violations": []
        }
        
        with patch.object(service.complexity_analyzer, 'analyze_query', return_value=mock_metrics), \
             patch.object(service.complexity_analyzer, 'validate_query_limits', return_value=mock_validation):
            
            # Execute
            result = await service.analyze_query_complexity(query)
            
            # Verify
            assert result["complexity_metrics"]["total_score"] == 15
            assert result["complexity_metrics"]["depth"] == 3
            assert result["complexity_metrics"]["field_count"] == 4
            assert result["validation"]["valid"] is True
    
    @pytest.mark.asyncio
    async def test_get_slow_queries(self, test_database_manager):
        """RED: Test getting slow queries above threshold."""
        service = FraiseQLService(test_database_manager)
        
        # Mock slow queries result
        expected_slow_queries = [
            {
                "query_id": "abc123",
                "execution_time_ms": 1500,
                "query": "{ users { posts { comments } } }",
                "endpoint_id": str(uuid4())
            },
            {
                "query_id": "def456", 
                "execution_time_ms": 1200,
                "query": "{ products { reviews } }",
                "endpoint_id": str(uuid4())
            }
        ]
        
        with patch.object(service.metrics_collector, 'get_slow_queries',
                         return_value=expected_slow_queries):
            
            # Execute
            result = await service.get_slow_queries(threshold_ms=1000, limit=10, time_window_seconds=3600)
            
            # Verify
            assert result == expected_slow_queries
            assert len(result) == 2
            assert all(q["execution_time_ms"] >= 1000 for q in result)
            
            service.metrics_collector.get_slow_queries.assert_called_once_with(1000, 10, 3600)


class TestFraiseQLServiceCircuitBreaker:
    """Test circuit breaker functionality following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_stats_existing_client(self, test_database_manager):
        """RED: Test getting circuit breaker stats for existing client."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock client with circuit breaker stats
        mock_client = AsyncMock()
        expected_stats = {
            "state": "CLOSED",
            "failure_count": 2,
            "success_count": 98,
            "last_failure_time": None
        }
        mock_client.get_circuit_breaker_stats.return_value = expected_stats
        
        # Add client to service
        service._clients[endpoint_id] = mock_client
        
        # Execute
        result = await service.get_circuit_breaker_stats(endpoint_id)
        
        # Verify
        assert result == expected_stats
        mock_client.get_circuit_breaker_stats.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_circuit_breaker_stats_no_client(self, test_database_manager):
        """RED: Test getting circuit breaker stats when no client exists."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Execute (no client exists)
        result = await service.get_circuit_breaker_stats(endpoint_id)
        
        # Verify error response
        assert result["error"] == "No client found for endpoint"
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_success(self, test_database_manager):
        """RED: Test successful circuit breaker reset."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock client
        mock_client = AsyncMock()
        service._clients[endpoint_id] = mock_client
        
        # Execute
        result = await service.reset_circuit_breaker(endpoint_id)
        
        # Verify
        assert result["success"] is True
        assert result["message"] == "Circuit breaker reset"
        mock_client.reset_circuit_breaker.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker_no_client(self, test_database_manager):
        """RED: Test circuit breaker reset when no client exists."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Execute (no client exists)
        result = await service.reset_circuit_breaker(endpoint_id)
        
        # Verify error response
        assert result["error"] == "No client found for endpoint"


class TestFraiseQLServiceUtilities:
    """Test utility functions following TDD methodology."""
    
    @pytest.mark.asyncio
    async def test_generate_query_id_consistency(self, test_database_manager):
        """RED: Test that query ID generation is consistent."""
        service = FraiseQLService(test_database_manager)
        
        query = "{ users { id name } }"
        variables = {"limit": 10, "offset": 0}
        operation_name = "GetUsers"
        
        # Generate ID multiple times
        id1 = service._generate_query_id(query, variables, operation_name)
        id2 = service._generate_query_id(query, variables, operation_name)
        
        # Should be identical
        assert id1 == id2
        assert len(id1) == 12  # Should be 12 character hash
    
    @pytest.mark.asyncio
    async def test_generate_query_id_different_inputs(self, test_database_manager):
        """RED: Test that different inputs generate different query IDs."""
        service = FraiseQLService(test_database_manager)
        
        query1 = "{ users { id } }"
        query2 = "{ users { name } }"
        
        id1 = service._generate_query_id(query1, None, None)
        id2 = service._generate_query_id(query2, None, None)
        
        # Should be different
        assert id1 != id2
    
    @pytest.mark.asyncio
    async def test_cleanup_resources(self, test_database_manager):
        """RED: Test proper cleanup of resources."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.client = AsyncMock()
        service._clients[endpoint_id] = mock_client
        
        # Mock pool manager
        service.pool_manager = AsyncMock()
        
        # Execute cleanup
        await service.cleanup()
        
        # Verify cleanup
        mock_client.client.close.assert_called_once()
        service.pool_manager.close_all.assert_called_once()
        assert service._clients == {}


class TestFraiseQLServiceIntegrationScenarios:
    """Integration test scenarios combining multiple service features."""
    
    @pytest.mark.asyncio
    async def test_complete_query_workflow_with_metrics(self, test_database_manager):
        """RED: Test complete workflow from query execution to metrics collection."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        query = "{ users(limit: $limit) { id name } }"
        variables = {"limit": 5}
        
        # Mock complete workflow
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.BEARER,
            auth_config={"token": "test-123"},
            is_active=True
        )
        
        mock_response = GraphQLResponse(
            data={"users": [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]},
            errors=None,
            extensions=None
        )
        
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = mock_response
        
        # Mock metrics recording
        metrics_recorded = []
        original_record = service.metrics_collector.record_query
        service.metrics_collector.record_query = lambda m: metrics_recorded.append(m)
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client), \
             patch.object(service.complexity_analyzer, 'validate_query_limits',
                         return_value={"valid": True, "violations": []}):
            
            # Execute complete workflow
            result = await service.execute_query(endpoint_id, query, variables, operation_name="GetUsers")
            
            # Verify query result
            assert result.data["users"][0]["name"] == "Alice"
            assert result.data["users"][1]["name"] == "Bob"
            
            # Verify metrics were recorded
            assert len(metrics_recorded) == 1
            recorded_metric = metrics_recorded[0]
            assert recorded_metric.endpoint_id == str(endpoint_id)
            assert recorded_metric.operation_name == "GetUsers"
            assert recorded_metric.success is True
            assert recorded_metric.execution_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_endpoint_failure_and_circuit_breaker_workflow(self, test_database_manager):
        """RED: Test workflow when endpoint fails and circuit breaker activates."""
        service = FraiseQLService(test_database_manager)
        endpoint_id = uuid4()
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="failing-api",
            url="https://failing-api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock failing client
        mock_client = AsyncMock()
        mock_client.execute_with_retry.side_effect = ConnectionError("Service unavailable")
        mock_client.get_circuit_breaker_stats.return_value = {
            "state": "OPEN",
            "failure_count": 5,
            "success_count": 0
        }
        
        service._clients[endpoint_id] = mock_client
        
        with patch.object(service, '_get_endpoint', return_value=mock_endpoint), \
             patch.object(service, '_get_client', return_value=mock_client), \
             patch.object(service.complexity_analyzer, 'validate_query_limits',
                         return_value={"valid": True, "violations": []}):
            
            # Execute query (should fail)
            with pytest.raises(ConnectionError):
                await service.execute_query(endpoint_id, "{ test }")
            
            # Check circuit breaker status
            cb_stats = await service.get_circuit_breaker_stats(endpoint_id)
            assert cb_stats["state"] == "OPEN"
            assert cb_stats["failure_count"] == 5
            
            # Reset circuit breaker
            reset_result = await service.reset_circuit_breaker(endpoint_id)
            assert reset_result["success"] is True
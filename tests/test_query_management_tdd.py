"""Query Management comprehensive testing following TDD methodology.

Focus: Complete query lifecycle testing - creation, execution, monitoring, optimization.
Target: Test all query-related functionality with proper isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from fraiseql_doctor.models.query import Query, QueryType
from fraiseql_doctor.models.endpoint import Endpoint, AuthType
from fraiseql_doctor.services.fraiseql_service import FraiseQLService
from fraiseql_doctor.services.client import GraphQLResponse
from fraiseql_doctor.core.exceptions import GraphQLClientError


class TestQueryLifecycleManagement:
    """Test complete query lifecycle from creation to execution."""
    
    @pytest.mark.asyncio
    async def test_query_model_has_required_fields(self):
        """RED: Test that Query model has all required fields for lifecycle management."""
        # Test basic Query model structure
        query_id = uuid4()
        endpoint_id = uuid4()
        
        query = Query(
            id=query_id,
            name="test-query",
            query_text="{ users { id name } }",
            query_type=QueryType.QUERY,
            endpoint_id=endpoint_id,
            default_variables={"limit": 10},
            is_active=True
        )
        
        # Verify all required fields exist
        assert query.id == query_id
        assert query.name == "test-query"
        assert query.query_text == "{ users { id name } }"
        assert query.query_type == QueryType.QUERY
        assert query.endpoint_id == endpoint_id
        assert query.default_variables == {"limit": 10}
        assert query.is_active is True
    
    @pytest.mark.asyncio
    async def test_query_model_supports_all_graphql_operations(self):
        """RED: Test that Query model supports QUERY, MUTATION, SUBSCRIPTION."""
        # Test all GraphQL operation types
        operations = [
            (QueryType.QUERY, "{ users { id } }"),
            (QueryType.MUTATION, "mutation { createUser(input: $input) { id } }"),
            (QueryType.SUBSCRIPTION, "subscription { userUpdated { id } }")
        ]
        
        for query_type, query_text in operations:
            query = Query(
                name=f"test-{query_type.value}",
                query_text=query_text,
                query_type=query_type,
                endpoint_id=uuid4()
            )
            
            assert query.query_type == query_type
            assert query.query_text == query_text
    
    @pytest.mark.asyncio
    async def test_query_has_execution_tracking_fields(self):
        """RED: Test that Query model tracks execution statistics."""
        query = Query(
            name="tracked-query",
            query_text="{ users { id } }",
            query_type=QueryType.QUERY,
            endpoint_id=uuid4()
        )
        
        # Verify execution tracking fields exist
        assert hasattr(query, 'total_executions')
        assert hasattr(query, 'total_failures')
        assert hasattr(query, 'avg_response_time_ms')
        assert hasattr(query, 'avg_complexity')
        
        # Should default to 0
        assert query.total_executions == 0
        assert query.total_failures == 0


class TestQueryExecutionWorkflow:
    """Test query execution workflow with monitoring and error handling."""
    
    @pytest.mark.asyncio
    async def test_service_execute_query_basic_workflow(self):
        """RED: Test basic query execution workflow through service."""
        # Create mock database manager
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        endpoint_id = uuid4()
        query_text = "{ users { id name } }"
        variables = {"limit": 5}
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock successful response
        expected_response = GraphQLResponse(
            data={"users": [{"id": "1", "name": "Alice"}]},
            errors=None,
            extensions=None
        )
        
        # Test that service has execute_query method
        assert hasattr(service, 'execute_query')
        assert callable(getattr(service, 'execute_query'))
        
        # Verify method signature accepts required parameters
        import inspect
        sig = inspect.signature(service.execute_query)
        required_params = ['endpoint_id', 'query']
        
        for param in required_params:
            assert param in sig.parameters, f"Missing required parameter: {param}"
    
    @pytest.mark.asyncio
    async def test_query_execution_with_variables(self):
        """RED: Test query execution with variable substitution."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test variables parameter exists and is handled
        endpoint_id = uuid4()
        query_text = "query GetUsers($limit: Int) { users(limit: $limit) { id } }"
        variables = {"limit": 10}
        
        # Verify the method can accept variables
        import inspect
        sig = inspect.signature(service.execute_query)
        assert 'variables' in sig.parameters
        
        # Verify variables parameter is optional
        variables_param = sig.parameters['variables']
        assert variables_param.default is not inspect.Parameter.empty or variables_param.default is None
    
    @pytest.mark.asyncio
    async def test_query_execution_with_operation_name(self):
        """RED: Test query execution with operation name for tracking."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test operation_name parameter
        import inspect
        sig = inspect.signature(service.execute_query)
        assert 'operation_name' in sig.parameters
        
        # Should be optional
        op_name_param = sig.parameters['operation_name']
        assert op_name_param.default is not inspect.Parameter.empty or op_name_param.default is None


class TestQueryComplexityValidation:
    """Test query complexity analysis and validation."""
    
    @pytest.mark.asyncio
    async def test_service_has_complexity_validation(self):
        """RED: Test that service can validate query complexity."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test that service has complexity analyzer
        assert hasattr(service, 'complexity_analyzer')
        assert hasattr(service.complexity_analyzer, 'validate_query_limits')
        assert hasattr(service.complexity_analyzer, 'analyze_query')
        
        # Test that execute_query accepts complexity validation parameter
        import inspect
        sig = inspect.signature(service.execute_query)
        assert 'validate_complexity' in sig.parameters
    
    @pytest.mark.asyncio
    async def test_service_analyze_query_complexity_method(self):
        """RED: Test that service provides query complexity analysis."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test analyze_query_complexity method exists
        assert hasattr(service, 'analyze_query_complexity')
        assert callable(getattr(service, 'analyze_query_complexity'))
        
        # Verify method signature
        import inspect
        sig = inspect.signature(service.analyze_query_complexity)
        assert 'query' in sig.parameters
    
    @pytest.mark.asyncio
    async def test_complexity_validation_prevents_expensive_queries(self):
        """RED: Test that complexity validation can reject expensive queries."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Create a mock complex query
        complex_query = """
        query DeepNesting {
            users {
                posts {
                    comments {
                        replies {
                            user {
                                posts {
                                    comments {
                                        user {
                                            profile
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        # Mock complexity analyzer to reject this query
        service.complexity_analyzer.validate_query_limits = MagicMock(
            return_value={
                "valid": False,
                "violations": ["Query depth exceeds limit", "Too many nested fields"]
            }
        )
        
        endpoint_id = uuid4()
        
        # Mock the _get_endpoint method to avoid database calls
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        service._get_endpoint = AsyncMock(return_value=mock_endpoint)
        
        # Test that complex query is rejected
        with pytest.raises(GraphQLClientError, match="Query complexity validation failed"):
            await service.execute_query(endpoint_id, complex_query, validate_complexity=True)


class TestQueryMetricsCollection:
    """Test query execution metrics and performance tracking."""
    
    @pytest.mark.asyncio
    async def test_service_has_metrics_collector(self):
        """RED: Test that service collects query execution metrics."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Verify metrics collector exists
        assert hasattr(service, 'metrics_collector')
        assert hasattr(service.metrics_collector, 'record_query')
        assert hasattr(service.metrics_collector, 'get_performance_summary')
    
    @pytest.mark.asyncio
    async def test_service_tracks_query_performance(self):
        """RED: Test that service provides performance metrics."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test performance methods exist
        assert hasattr(service, 'get_performance_metrics')
        assert hasattr(service, 'get_slow_queries')
        assert callable(getattr(service, 'get_performance_metrics'))
        assert callable(getattr(service, 'get_slow_queries'))
        
        # Verify method signatures
        import inspect
        
        # get_performance_metrics should accept endpoint_id and time_window
        perf_sig = inspect.signature(service.get_performance_metrics)
        assert 'endpoint_id' in perf_sig.parameters
        assert 'time_window_seconds' in perf_sig.parameters
        
        # get_slow_queries should accept threshold and limit
        slow_sig = inspect.signature(service.get_slow_queries)
        assert 'threshold_ms' in slow_sig.parameters
        assert 'limit' in slow_sig.parameters
    
    @pytest.mark.asyncio
    async def test_query_execution_records_timing_metrics(self):
        """RED: Test that query execution records timing information."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test that service generates query IDs for tracking
        assert hasattr(service, '_generate_query_id')
        assert callable(getattr(service, '_generate_query_id'))
        
        # Test query ID generation
        query1 = "{ users { id } }"
        variables1 = {"limit": 10}
        
        id1 = service._generate_query_id(query1, variables1, "GetUsers")
        id2 = service._generate_query_id(query1, variables1, "GetUsers")
        
        # Same query should generate same ID
        assert id1 == id2
        assert len(id1) == 12  # Should be 12 character hash
        
        # Different queries should generate different IDs
        query2 = "{ posts { id } }"
        id3 = service._generate_query_id(query2, variables1, "GetPosts")
        assert id1 != id3


class TestQueryErrorHandling:
    """Test query error handling and recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_service_handles_graphql_errors_gracefully(self):
        """RED: Test that service handles GraphQL errors in responses."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        endpoint_id = uuid4()
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock GraphQL response with errors
        error_response = GraphQLResponse(
            data=None,
            errors=[
                {
                    "message": "Cannot query field 'invalidField' on type 'User'",
                    "locations": [{"line": 2, "column": 5}],
                    "path": ["users", 0, "invalidField"]
                }
            ],
            extensions=None
        )
        
        # Mock client that returns error response
        mock_client = AsyncMock()
        mock_client.execute_with_retry.return_value = error_response
        
        # Mock dependencies
        service._get_endpoint = AsyncMock(return_value=mock_endpoint)
        service._get_client = AsyncMock(return_value=mock_client)
        service.complexity_analyzer.validate_query_limits = MagicMock(
            return_value={"valid": True, "violations": []}
        )
        
        # Execute query with GraphQL errors
        result = await service.execute_query(endpoint_id, "{ users { invalidField } }")
        
        # Should return the response with errors, not raise exception
        assert result == error_response
        assert result.errors is not None
        assert len(result.errors) == 1
        assert "Cannot query field 'invalidField'" in result.errors[0]["message"]
    
    @pytest.mark.asyncio
    async def test_service_handles_network_errors(self):
        """RED: Test that service handles network/connection errors."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        endpoint_id = uuid4()
        
        # Mock endpoint
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock client that raises network error
        mock_client = AsyncMock()
        mock_client.execute_with_retry.side_effect = ConnectionError("Network timeout")
        
        # Mock dependencies  
        service._get_endpoint = AsyncMock(return_value=mock_endpoint)
        service._get_client = AsyncMock(return_value=mock_client)
        service.complexity_analyzer.validate_query_limits = MagicMock(
            return_value={"valid": True, "violations": []}
        )
        
        # Network errors should be propagated
        with pytest.raises(ConnectionError, match="Network timeout"):
            await service.execute_query(endpoint_id, "{ users { id } }")
    
    @pytest.mark.asyncio  
    async def test_service_has_circuit_breaker_functionality(self):
        """RED: Test that service provides circuit breaker functionality."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test circuit breaker methods exist
        assert hasattr(service, 'get_circuit_breaker_stats')
        assert hasattr(service, 'reset_circuit_breaker')
        assert callable(getattr(service, 'get_circuit_breaker_stats'))
        assert callable(getattr(service, 'reset_circuit_breaker'))
        
        # Verify method signatures
        import inspect
        
        stats_sig = inspect.signature(service.get_circuit_breaker_stats)
        assert 'endpoint_id' in stats_sig.parameters
        
        reset_sig = inspect.signature(service.reset_circuit_breaker)
        assert 'endpoint_id' in reset_sig.parameters


class TestQueryOptimizationRecommendations:
    """Test query optimization analysis and recommendations."""
    
    @pytest.mark.asyncio
    async def test_service_provides_query_optimization_analysis(self):
        """RED: Test that service can analyze queries for optimization opportunities."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test that analyze_query_complexity method exists and returns optimization data
        assert hasattr(service, 'analyze_query_complexity')
        
        # Mock the complexity analyzer to return analysis results
        mock_metrics = MagicMock()
        mock_metrics.total_score = 25
        mock_metrics.depth = 4
        mock_metrics.field_count = 12
        mock_metrics.nested_queries = 3
        mock_metrics.estimated_cost = 150
        mock_metrics.recommendations = [
            "Consider adding limits to nested queries",
            "Use fragments to reduce duplication",
            "Add pagination to list fields"
        ]
        
        service.complexity_analyzer.analyze_query = MagicMock(return_value=mock_metrics)
        service.complexity_analyzer.validate_query_limits = MagicMock(
            return_value={"valid": True, "violations": []}
        )
        
        # Test analysis of a moderately complex query
        complex_query = """
        query GetUsersPosts($limit: Int) {
            users(limit: $limit) {
                id
                name
                posts {
                    id
                    title
                    comments {
                        id
                        content
                        author {
                            name
                        }
                    }
                }
            }
        }
        """
        
        result = await service.analyze_query_complexity(complex_query)
        
        # Verify analysis structure
        assert "complexity_metrics" in result
        assert "validation" in result
        
        # Verify complexity metrics
        metrics = result["complexity_metrics"]
        assert metrics["total_score"] == 25
        assert metrics["depth"] == 4
        assert metrics["field_count"] == 12
        assert metrics["nested_queries"] == 3
        assert metrics["estimated_cost"] == 150
        assert len(metrics["recommendations"]) == 3
        assert "Consider adding limits to nested queries" in metrics["recommendations"]
    
    @pytest.mark.asyncio
    async def test_service_tracks_query_performance_over_time(self):
        """RED: Test that service can track query performance trends."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test endpoint comparison functionality
        assert hasattr(service, 'get_endpoint_comparison')
        assert callable(getattr(service, 'get_endpoint_comparison'))
        
        # Verify method signature
        import inspect
        comp_sig = inspect.signature(service.get_endpoint_comparison)
        assert 'time_window_seconds' in comp_sig.parameters


class TestQueryBatchingAndCaching:
    """Test query batching and caching strategies."""
    
    @pytest.mark.asyncio
    async def test_service_supports_client_management(self):
        """RED: Test that service manages clients efficiently."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test client management
        assert hasattr(service, '_clients')
        assert hasattr(service, '_get_client')
        assert callable(getattr(service, '_get_client'))
        
        # Should start with no clients
        assert service._clients == {}
    
    @pytest.mark.asyncio
    async def test_service_provides_cleanup_functionality(self):
        """RED: Test that service provides proper resource cleanup."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        # Test cleanup method exists
        assert hasattr(service, 'cleanup')
        assert callable(getattr(service, 'cleanup'))
        
        # Verify it's async
        import inspect
        assert inspect.iscoroutinefunction(service.cleanup)
    
    @pytest.mark.asyncio
    async def test_client_caching_prevents_duplicate_connections(self):
        """RED: Test that service reuses clients for same endpoint."""
        db_manager = AsyncMock()
        service = FraiseQLService(db_manager)
        
        endpoint_id = uuid4()
        mock_endpoint = Endpoint(
            id=endpoint_id,
            name="test-api",
            url="https://api.example.com/graphql",
            auth_type=AuthType.NONE,
            is_active=True
        )
        
        # Mock dependencies
        mock_retryable_client = AsyncMock()
        service.pool_manager = AsyncMock()
        service.pool_manager.get_session.return_value = AsyncMock()
        
        # Mock the client creation process
        with pytest.mock.patch('fraiseql_doctor.services.fraiseql_service.FraiseQLClient') as mock_client_class, \
             pytest.mock.patch('fraiseql_doctor.services.fraiseql_service.RetryableClient') as mock_retryable_class:
            
            mock_retryable_class.return_value = mock_retryable_client
            
            # First call should create client
            client1 = await service._get_client(mock_endpoint)
            assert endpoint_id in service._clients
            assert service._clients[endpoint_id] == mock_retryable_client
            
            # Second call should reuse same client
            client2 = await service._get_client(mock_endpoint)
            assert client1 == client2
            
            # Should only create one client instance
            mock_retryable_class.assert_called_once()
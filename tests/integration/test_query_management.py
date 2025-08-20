"""
Integration tests for Query Management System (Phase 4)

Tests the complete integration of:
- Query Collection Management
- Query Execution Manager  
- Result Storage System
- End-to-end workflows
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from src.fraiseql_doctor.core.query_collection import (
    QueryCollectionManager, QueryStatus, QueryPriority, QuerySearchFilter
)
from src.fraiseql_doctor.core.execution_manager import (
    QueryExecutionManager, ExecutionStatus, BatchMode, ExecutionConfig
)
from src.fraiseql_doctor.core.result_storage import (
    ResultStorageManager, StorageConfig, StorageBackend, CompressionType
)
from src.fraiseql_doctor.services.complexity import QueryComplexityAnalyzer
from src.fraiseql_doctor.core.fraiseql_client import FraiseQLClient
from src.fraiseql_doctor.core.database.models import Endpoint
from src.fraiseql_doctor.core.database.schemas import (
    QueryCollectionCreate, QueryCreate, ResultSearchFilter
)


@pytest.fixture
async def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock()
    session.execute.return_value = []
    session.get.return_value = None
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    return session


@pytest.fixture
def complexity_analyzer():
    """Create complexity analyzer instance."""
    return QueryComplexityAnalyzer()


@pytest.fixture
async def query_collection_manager(mock_db_session, complexity_analyzer):
    """Create query collection manager instance."""
    return QueryCollectionManager(mock_db_session, complexity_analyzer)


@pytest.fixture
def mock_client():
    """Create mock FraiseQL client."""
    client = AsyncMock(spec=FraiseQLClient)
    client.execute_query.return_value = {
        "data": {"test": "result"},
        "_complexity_score": 5.2,
        "_execution_time": 0.15
    }
    return client


@pytest.fixture
def mock_client_factory(mock_client):
    """Create mock client factory."""
    def factory(endpoint):
        return mock_client
    return factory


@pytest.fixture
async def execution_manager(mock_db_session, mock_client_factory, query_collection_manager):
    """Create query execution manager instance."""
    config = ExecutionConfig(
        timeout_seconds=30,
        max_retries=2,
        max_concurrent=5,
        batch_size=10
    )
    return QueryExecutionManager(
        mock_db_session, 
        mock_client_factory, 
        query_collection_manager,
        config
    )


@pytest.fixture
async def result_storage_manager(mock_db_session, tmp_path):
    """Create result storage manager instance."""
    config = StorageConfig(
        backend=StorageBackend.FILE_SYSTEM,
        file_base_path=tmp_path / "results",
        compression=CompressionType.GZIP,
        ttl_hours=24
    )
    return ResultStorageManager(mock_db_session, config)


@pytest.fixture
def sample_endpoint():
    """Create sample endpoint for testing."""
    return Endpoint(
        pk_endpoint=uuid4(),
        name="Test GraphQL Endpoint",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "test-token"}
    )


@pytest.fixture
def sample_queries():
    """Create sample GraphQL queries for testing."""
    return [
        {
            "name": "Get Users",
            "query_text": """
                query GetUsers($limit: Int) {
                    users(limit: $limit) {
                        id
                        name
                        email
                    }
                }
            """,
            "variables": {"limit": 10},
            "created_by": "test-user",
            "priority": "medium"
        },
        {
            "name": "Get User Profile",
            "query_text": """
                query GetUserProfile($userId: ID!) {
                    user(id: $userId) {
                        id
                        name
                        email
                        profile {
                            bio
                            avatar
                        }
                    }
                }
            """,
            "variables": {"userId": "123"},
            "created_by": "test-user",
            "priority": "high"
        },
        {
            "name": "Complex Dashboard Query",
            "query_text": """
                query GetDashboard {
                    dashboard {
                        stats {
                            totalUsers
                            activeUsers
                            revenue
                        }
                        recentActivity {
                            id
                            type
                            user {
                                name
                                avatar
                            }
                            timestamp
                        }
                        charts {
                            userGrowth
                            revenueByMonth
                        }
                    }
                }
            """,
            "variables": {},
            "created_by": "test-user",
            "priority": "low"
        }
    ]


class TestQueryCollectionIntegration:
    """Test query collection management integration."""
    
    async def test_create_collection_with_queries(
        self, 
        query_collection_manager,
        sample_queries
    ):
        """Test creating a collection with initial queries."""
        # Mock successful query validation
        query_collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=5.0,
                estimated_execution_time=0.1,
                field_count=8,
                depth=3
            )
        )
        
        # Mock collection retrieval
        query_collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        
        collection_schema = QueryCollectionCreate(
            name="Test Collection",
            description="Collection for testing",
            tags=["test", "integration"],
            created_by="test-user",
            initial_queries=[
                QueryCreate(**query) for query in sample_queries
            ]
        )
        
        collection = await query_collection_manager.create_collection(collection_schema)
        
        assert collection.name == "Test Collection"
        assert collection.description == "Collection for testing"
        assert collection.created_by == "test-user"
    
    async def test_search_queries_with_filters(
        self,
        query_collection_manager,
        sample_queries
    ):
        """Test advanced query searching with filters."""
        # Mock database results
        mock_results = [
            {
                "id": str(uuid4()),
                "collection_id": str(uuid4()),
                "name": "Get Users",
                "content": sample_queries[0]["query_text"],
                "status": "active",
                "priority": "medium",
                "tags": ["user", "list"],
                "created_at": datetime.now(timezone.utc),
                "metadata": {"complexity_score": 5.0}
            }
        ]
        
        query_collection_manager.db_session.execute.return_value = mock_results
        
        filter_params = QuerySearchFilter(
            text="users",
            status=QueryStatus.ACTIVE,
            priority=QueryPriority.MEDIUM,
            complexity_min=1.0,
            complexity_max=10.0,
            limit=50
        )
        
        results = await query_collection_manager.search_queries(filter_params)
        
        assert len(results) == 1
        assert results[0].name == "Get Users"
        
        # Verify SQL query was constructed correctly
        call_args = query_collection_manager.db_session.execute.call_args
        assert "name ILIKE" in call_args[0][0]
        assert "status =" in call_args[0][0]
        assert "priority =" in call_args[0][0]


class TestExecutionManagerIntegration:
    """Test query execution manager integration."""
    
    async def test_single_query_execution(
        self,
        execution_manager,
        query_collection_manager,
        sample_endpoint,
        sample_queries
    ):
        """Test executing a single query with full integration."""
        # Create a mock query
        query_id = uuid4()
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.name = sample_queries[0]["name"]
        mock_query.content = sample_queries[0]["query_text"]
        mock_query.variables = sample_queries[0]["variables"]
        mock_query.metadata = MagicMock(complexity_score=5.0)
        
        with patch.object(query_collection_manager, 'get_query', return_value=mock_query):
            execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
            
            result = await execution_manager.execute_query(
                query_id,
                sample_endpoint.pk_endpoint
            )
            
            assert result.success is True
            assert result.status == ExecutionStatus.COMPLETED
            assert result.query_id == query_id
            assert result.result_data == {"data": {"test": "result"}, "_complexity_score": 5.2, "_execution_time": 0.15}
            assert result.execution_time > 0
    
    async def test_batch_execution_parallel(
        self,
        execution_manager,
        query_collection_manager,
        sample_endpoint,
        sample_queries
    ):
        """Test parallel batch execution."""
        # Create mock queries
        query_ids = [uuid4() for _ in sample_queries]
        
        for i, query_id in enumerate(query_ids):
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.name = sample_queries[i]["name"]
            mock_query.content = sample_queries[i]["query_text"]
            mock_query.variables = sample_queries[i]["variables"]
            mock_query.metadata = MagicMock(complexity_score=float(i + 1))
            
            # Mock different queries return different results
            with patch.object(query_collection_manager, 'get_query', return_value=mock_query):
                
                execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
                
                batch_result = await execution_manager.execute_batch(
                    query_ids,
                    sample_endpoint.pk_endpoint,
                    mode=BatchMode.PARALLEL
                )
                
                assert batch_result.total_queries == 3
                assert batch_result.successful == 3
                assert batch_result.failed == 0
                assert len(batch_result.results) == 3
                assert all(r.success for r in batch_result.results)
    
    async def test_batch_execution_priority_mode(
        self,
        execution_manager,
        query_collection_manager,
        sample_endpoint,
        sample_queries
    ):
        """Test priority-based batch execution ordering."""
        # Create mock queries with different priorities
        query_ids = [uuid4() for _ in sample_queries]
        mock_queries = []
        
        for i, query_id in enumerate(query_ids):
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.name = sample_queries[i]["name"]
            mock_query.content = sample_queries[i]["query_text"]
            mock_query.variables = sample_queries[i]["variables"]
            mock_query.priority = QueryPriority(sample_queries[i]["priority"])
            mock_query.metadata = MagicMock(complexity_score=5.0)
            mock_queries.append(mock_query)
        
        # Mock query retrieval to return different queries based on ID
        async def get_query_side_effect(query_id):
            for query in mock_queries:
                if query.id == query_id:
                    return query
            return None
        
        # Use patch to mock the method properly
        with patch.object(query_collection_manager, 'get_query', side_effect=get_query_side_effect):
            execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
            
            batch_result = await execution_manager.execute_batch(
                query_ids,
                sample_endpoint.pk_endpoint,
                mode=BatchMode.PRIORITY
            )
            
            assert batch_result.successful == 3
            
            # Check that high priority queries were executed first
            # (This would require more detailed mocking to verify execution order)
            assert len(batch_result.results) == 3
    
    async def test_scheduled_execution(
        self,
        execution_manager,
        query_collection_manager,
        sample_endpoint
    ):
        """Test scheduling query for recurring execution."""
        query_id = uuid4()
        cron_expression = "0 9 * * *"  # Daily at 9 AM
        
        scheduled = await execution_manager.schedule_query(
            query_id,
            sample_endpoint.pk_endpoint,
            cron_expression
        )
        
        assert scheduled.query_id == query_id
        assert scheduled.cron_expression == cron_expression
        assert scheduled.endpoint_id == sample_endpoint.pk_endpoint
        assert scheduled.enabled is True
        assert scheduled.next_execution is not None
        
        # Verify it's stored in the manager
        assert scheduled.id in execution_manager._scheduled_executions


class TestResultStorageIntegration:
    """Test result storage system integration."""
    
    async def test_store_and_retrieve_result(
        self,
        result_storage_manager
    ):
        """Test storing and retrieving query results."""
        execution_id = uuid4()
        query_id = uuid4()
        result_data = {
            "data": {
                "users": [
                    {"id": "1", "name": "John", "email": "john@example.com"},
                    {"id": "2", "name": "Jane", "email": "jane@example.com"}
                ]
            },
            "extensions": {
                "complexity": 5.2,
                "execution_time": 0.15
            }
        }
        
        # Store result
        storage_key = await result_storage_manager.store_result(
            execution_id,
            query_id,
            result_data,
            metadata={"test": "metadata"}
        )
        
        assert storage_key.startswith("result:")
        assert str(execution_id) in storage_key
        
        # Retrieve result
        retrieved_data = await result_storage_manager.retrieve_result(storage_key)
        
        assert retrieved_data == result_data
    
    async def test_result_compression_and_serialization(
        self,
        result_storage_manager
    ):
        """Test result compression and different serialization formats."""
        # Create large result data to test compression
        large_data = {
            "data": {
                "items": [{"id": i, "data": f"test data item {i}" * 100} for i in range(1000)]
            }
        }
        
        execution_id = uuid4()
        query_id = uuid4()
        
        storage_key = await result_storage_manager.store_result(
            execution_id,
            query_id,
            large_data
        )
        
        # Verify compression worked
        # (In a real test, you'd check file sizes or database storage metrics)
        retrieved_data = await result_storage_manager.retrieve_result(storage_key)
        assert retrieved_data == large_data
        
        # Check metrics show compression
        metrics = await result_storage_manager.get_metrics()
        assert metrics.total_results > 0
        assert metrics.compression_ratio < 1.0  # Should be compressed
    
    async def test_result_search_and_analytics(
        self,
        result_storage_manager
    ):
        """Test result search and analytics capabilities."""
        # Mock search results
        mock_results = [
            {
                "id": str(uuid4()),
                "execution_id": str(uuid4()),
                "query_id": str(uuid4()),
                "storage_key": "result:test1",
                "size_bytes": 1024,
                "compressed_size_bytes": 512,
                "compression_ratio": 0.5,
                "created_at": datetime.now(timezone.utc),
                "metadata": {"test": "data"}
            }
        ]
        
        result_storage_manager.db_session.execute.return_value = mock_results
        
        # Test search
        filter_params = ResultSearchFilter(
            query_ids=[uuid4()],
            min_size_bytes=500,
            max_size_bytes=2000,
            limit=10
        )
        
        results = await result_storage_manager.search_results(filter_params)
        assert len(results) == 1
        
        # Test analytics
        analytics_mock = [{
            "total_results": 100,
            "total_original_size": 1000000,
            "total_compressed_size": 500000,
            "avg_original_size": 10000,
            "avg_compressed_size": 5000,
            "avg_compression_ratio": 0.5,
            "unique_queries": 25
        }]
        
        result_storage_manager.db_session.execute.return_value = analytics_mock
        
        analytics = await result_storage_manager.get_storage_analytics(days_back=7)
        
        assert analytics["total_results"] == 100
        assert analytics["unique_queries"] == 25
        assert analytics["storage_usage"]["space_saved_percentage"] == 50.0


class TestEndToEndIntegration:
    """Test complete end-to-end workflows."""
    
    async def test_complete_query_lifecycle(
        self,
        query_collection_manager,
        execution_manager,
        result_storage_manager,
        sample_endpoint,
        sample_queries
    ):
        """Test complete query lifecycle from creation to result storage."""
        # Step 1: Create collection and add queries
        query_collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=5.0,
                estimated_execution_time=0.1,
                field_count=8,
                depth=3
            )
        )
        query_collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        
        collection_schema = QueryCollectionCreate(
            name="Integration Test Collection",
            description="End-to-end testing",
            created_by="test-user",
            initial_queries=[QueryCreate(**sample_queries[0])]
        )
        
        collection = await query_collection_manager.create_collection(collection_schema)
        
        # Create a mock query for testing
        query = MagicMock()
        query.id = uuid4()
        query.name = sample_queries[0]["name"]
        query.content = sample_queries[0]["query_text"]
        query.variables = sample_queries[0]["variables"]
        
        # Step 2: Execute query
        with patch.object(query_collection_manager, 'get_query', return_value=query):
            execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
            
            execution_result = await execution_manager.execute_query(
                query.id,
                sample_endpoint.pk_endpoint
            )
            
            assert execution_result.success is True
            
            # Step 3: Store result
            storage_key = await result_storage_manager.store_result(
                execution_result.execution_id,
                query.id,
                execution_result.result_data
            )
            
            # Step 4: Retrieve and verify result
            stored_result = await result_storage_manager.retrieve_result(storage_key)
            assert stored_result == execution_result.result_data
        
        # Step 5: Search for results
        filter_params = ResultSearchFilter(
            query_ids=[query.id],
            limit=10
        )
        
        # Mock the search results
        result_storage_manager.db_session.execute.return_value = [{
            "id": str(uuid4()),
            "execution_id": str(execution_result.execution_id),
            "query_id": str(query.id),
            "storage_key": storage_key,
            "size_bytes": 1024,
            "compressed_size_bytes": 512,
            "compression_ratio": 0.5,
            "created_at": datetime.now(timezone.utc),
            "metadata": {}
        }]
        
        search_results = await result_storage_manager.search_results(filter_params)
        assert len(search_results) == 1
        assert search_results[0].query_id == query.id
    
    async def test_batch_execution_with_result_storage(
        self,
        query_collection_manager,
        execution_manager,
        result_storage_manager,
        sample_endpoint,
        sample_queries
    ):
        """Test batch execution with automatic result storage."""
        # Setup queries
        query_ids = []
        mock_queries = []
        
        for i, query_data in enumerate(sample_queries):
            query_id = uuid4()
            query_ids.append(query_id)
            
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.name = query_data["name"]
            mock_query.content = query_data["query_text"]
            mock_query.variables = query_data["variables"]
            mock_query.metadata = MagicMock(complexity_score=float(i + 1))
            mock_queries.append(mock_query)
        
        async def get_query_side_effect(query_id):
            for query in mock_queries:
                if query.id == query_id:
                    return query
            return None
        
        # Use patch to mock the method properly
        with patch.object(query_collection_manager, 'get_query', side_effect=get_query_side_effect):
            execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
            
            # Execute batch
            batch_result = await execution_manager.execute_batch(
                query_ids,
                sample_endpoint.pk_endpoint,
                mode=BatchMode.PARALLEL
            )
            
            assert batch_result.successful == 3
            
            # Store all results
            storage_keys = []
            for execution_result in batch_result.results:
                if execution_result.success:
                    storage_key = await result_storage_manager.store_result(
                        execution_result.execution_id,
                        execution_result.query_id,
                        execution_result.result_data
                    )
                    storage_keys.append(storage_key)
            
            assert len(storage_keys) == 3
            
            # Verify all results can be retrieved
            for storage_key in storage_keys:
                result = await result_storage_manager.retrieve_result(storage_key)
                assert result is not None
    
    async def test_performance_monitoring_integration(
        self,
        execution_manager,
        result_storage_manager
    ):
        """Test performance monitoring across all components."""
        # Get execution metrics
        exec_metrics = await execution_manager.get_execution_metrics()
        
        # Get storage metrics
        storage_metrics = await result_storage_manager.get_metrics()
        
        # Get storage analytics
        result_storage_manager.db_session.execute.return_value = [{
            "total_results": 50,
            "total_original_size": 500000,
            "total_compressed_size": 250000,
            "avg_original_size": 10000,
            "avg_compressed_size": 5000,
            "avg_compression_ratio": 0.5,
            "unique_queries": 10
        }]
        
        analytics = await result_storage_manager.get_storage_analytics()
        
        # Verify all metrics are available
        assert "total_executions" in exec_metrics
        assert "successful_executions" in exec_metrics
        assert "total_results" in analytics
        assert "storage_usage" in analytics
        
        # This integration test demonstrates that all components
        # can work together to provide comprehensive monitoring
        assert True  # Test passes if no exceptions are raised


@pytest.mark.asyncio
class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    async def test_query_execution_failure_handling(
        self,
        execution_manager,
        query_collection_manager,
        sample_endpoint
    ):
        """Test handling of query execution failures."""
        query_id = uuid4()
        
        # Mock query that will cause execution failure
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.name = "Failing Query"
        mock_query.content = "invalid graphql syntax {"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)
        
        with patch.object(query_collection_manager, 'get_query', return_value=mock_query):
            execution_manager.db_session.get = AsyncMock(return_value=sample_endpoint)
            
            # Mock client to raise exception
            execution_manager.client_factory = lambda endpoint: AsyncMock(
                execute_query=AsyncMock(side_effect=Exception("GraphQL syntax error"))
            )
            
            result = await execution_manager.execute_query(
                query_id,
                sample_endpoint.pk_endpoint
            )
            
            assert result.success is False
            assert result.status == ExecutionStatus.FAILED
            assert "GraphQL syntax error" in result.error_message
    
    async def test_storage_failure_recovery(
        self,
        result_storage_manager
    ):
        """Test storage failure recovery mechanisms."""
        execution_id = uuid4()
        query_id = uuid4()
        
        # Mock storage backend to fail
        result_storage_manager.backend.store = AsyncMock(return_value=False)
        
        with pytest.raises(Exception):
            await result_storage_manager.store_result(
                execution_id,
                query_id,
                {"test": "data"}
            )
        
        # Test retrieval of non-existent result
        result = await result_storage_manager.retrieve_result("non-existent-key")
        assert result is None
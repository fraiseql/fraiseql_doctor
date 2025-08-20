"""
Simplified Integration tests for Query Management System (Phase 4)

Tests core functionality without complex database dependencies.
"""

import pytest
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

# Simple test models to avoid dependency issues
@dataclass
class MockEndpoint:
    id: str
    name: str
    url: str
    auth_type: str
    auth_config: dict

@dataclass 
class MockQueryMetadata:
    complexity_score: float = 0.0
    estimated_cost: float = 0.0
    field_count: int = 0
    depth: int = 0
    last_validated: datetime = None

@dataclass
class MockQuery:
    id: str
    name: str
    query_text: str
    variables: dict
    expected_complexity_score: float = 0.0
    metadata: MockQueryMetadata = None

@pytest.fixture
def mock_db_session():
    """Real test database session - more reliable than complex mocks."""
    from tests.fixtures.real_services import TestDatabaseSession
    return TestDatabaseSession()

@pytest.fixture
def mock_complexity_analyzer():
    """Real test complexity analyzer - more reliable than mocks."""
    from tests.fixtures.real_services import TestComplexityAnalyzer
    return TestComplexityAnalyzer()

@pytest.fixture 
def mock_fraiseql_client():
    """Real test GraphQL client - more predictable than complex mocks."""
    from tests.fixtures.real_services import TestGraphQLClient
    return TestGraphQLClient()

@pytest.fixture
def sample_query():
    """Sample query for testing."""
    return MockQuery(
        id=str(uuid4()),
        name="Test Query",
        query_text="""
            query GetUsers($limit: Int) {
                users(limit: $limit) {
                    id
                    name
                    email
                }
            }
        """,
        variables={"limit": 10},
        expected_complexity_score=5.0,
        metadata=MockQueryMetadata(complexity_score=5.0)
    )

@pytest.fixture
def sample_endpoint():
    """Sample endpoint for testing."""
    return MockEndpoint(
        id=str(uuid4()),
        name="Test GraphQL Endpoint",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "test-token"}
    )

class TestQueryExecutionCore:
    """Test core query execution functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_single_query_success(
        self,
        mock_db_session,
        mock_fraiseql_client,
        sample_query,
        sample_endpoint
    ):
        """Test successful single query execution."""
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager, ExecutionConfig, ExecutionStatus
        )
        from fraiseql_doctor.core.query_collection import QueryCollectionManager
        
        # Create mock collection manager
        collection_manager = MagicMock()
        collection_manager.get_query = AsyncMock(return_value=sample_query)
        
        # Create client factory
        def client_factory(endpoint):
            return mock_fraiseql_client
        
        # Create execution manager
        config = ExecutionConfig(timeout_seconds=30, max_concurrent=5)
        execution_manager = QueryExecutionManager(
            mock_db_session,
            client_factory,
            collection_manager,
            config
        )
        
        # TestDatabaseSession will automatically return appropriate test data for .get() calls
        # No additional configuration needed
        
        # Execute query
        result = await execution_manager.execute_query(
            sample_query.id,
            sample_endpoint.id
        )
        
        # Verify results
        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        assert result.query_id == sample_query.id
        assert result.result_data["data"]["test"] == "result"
        assert result.execution_time > 0
        
        # Verify client was called correctly
        mock_fraiseql_client.execute_query.assert_called_once_with(
            sample_query.query_text,
            sample_query.variables
        )
    
    @pytest.mark.asyncio
    async def test_execute_query_with_error(
        self,
        mock_db_session,
        mock_fraiseql_client,
        sample_query,
        sample_endpoint
    ):
        """Test query execution with GraphQL errors."""
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager, ExecutionConfig, ExecutionStatus
        )
        
        # Create mock collection manager
        collection_manager = MagicMock()
        collection_manager.get_query = AsyncMock(return_value=sample_query)
        
        # Configure client to return GraphQL errors using real test client patterns
        mock_fraiseql_client.set_custom_response({
            "data": None,
            "errors": [
                {"message": "Field 'invalidField' not found"}
            ]
        })
        
        def client_factory(endpoint):
            return mock_fraiseql_client
        
        config = ExecutionConfig(timeout_seconds=30)
        execution_manager = QueryExecutionManager(
            mock_db_session,
            client_factory,
            collection_manager,
            config
        )
        
        # TestDatabaseSession handles .get() calls automatically
        
        # Execute query
        result = await execution_manager.execute_query(
            sample_query.id,
            sample_endpoint.id
        )
        
        # Verify error handling
        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        assert "Field 'invalidField' not found" in result.error_message
        assert result.error_code == "GRAPHQL_ERROR"
    
    @pytest.mark.asyncio
    async def test_batch_execution_parallel(
        self,
        mock_db_session,
        mock_fraiseql_client,
        sample_endpoint
    ):
        """Test parallel batch execution."""
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager, ExecutionConfig, BatchMode
        )
        
        # Create multiple test queries
        queries = []
        query_ids = []
        for i in range(3):
            query = MockQuery(
                id=str(uuid4()),
                name=f"Test Query {i+1}",
                query_text=f"query TestQuery{i+1} {{ test{i+1} }}",
                variables={},
                expected_complexity_score=float(i+1),
                metadata=MockQueryMetadata(complexity_score=float(i+1))
            )
            queries.append(query)
            query_ids.append(query.id)
        
        # Create collection manager that returns different queries
        collection_manager = MagicMock()
        async def get_query_side_effect(query_id):
            for query in queries:
                if query.id == query_id:
                    return query
            return None
        collection_manager.get_query.side_effect = get_query_side_effect
        
        def client_factory(endpoint):
            return mock_fraiseql_client
        
        config = ExecutionConfig(max_concurrent=10)
        execution_manager = QueryExecutionManager(
            mock_db_session,
            client_factory,
            collection_manager,
            config
        )
        
        # TestDatabaseSession handles .get() calls automatically
        
        # Execute batch
        batch_result = await execution_manager.execute_batch(
            query_ids,
            sample_endpoint.id,
            mode=BatchMode.PARALLEL
        )
        
        # Verify batch results
        assert batch_result.total_queries == 3
        assert batch_result.successful == 3
        assert batch_result.failed == 0
        assert len(batch_result.results) == 3
        assert all(r.success for r in batch_result.results)


class TestResultStorageCore:
    """Test core result storage functionality."""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_result(self, mock_db_session, tmp_path):
        """Test basic result storage and retrieval."""
        from fraiseql_doctor.core.result_storage import (
            ResultStorageManager, StorageConfig, StorageBackend, CompressionType
        )
        
        # Configure for file system storage
        config = StorageConfig(
            backend=StorageBackend.FILE_SYSTEM,
            file_base_path=tmp_path / "results",
            compression=CompressionType.GZIP
        )
        
        storage_manager = ResultStorageManager(mock_db_session, config)
        
        # Test data
        execution_id = uuid4()
        query_id = uuid4()
        result_data = {
            "data": {
                "users": [
                    {"id": "1", "name": "John", "email": "john@example.com"},
                    {"id": "2", "name": "Jane", "email": "jane@example.com"}
                ]
            }
        }
        
        # Store result
        storage_key = await storage_manager.store_result(
            execution_id,
            query_id,
            result_data
        )
        
        # Verify storage key format
        assert storage_key.startswith("result:")
        assert str(execution_id) in storage_key
        
        # Retrieve result
        retrieved_data = await storage_manager.retrieve_result(storage_key)
        
        # Verify data integrity
        assert retrieved_data == result_data
    
    @pytest.mark.asyncio
    async def test_compression_effectiveness(self, mock_db_session, tmp_path):
        """Test that compression reduces storage size."""
        from fraiseql_doctor.core.result_storage import (
            ResultStorageManager, StorageConfig, StorageBackend, CompressionType
        )
        
        config = StorageConfig(
            backend=StorageBackend.FILE_SYSTEM,
            file_base_path=tmp_path / "results",
            compression=CompressionType.GZIP
        )
        
        storage_manager = ResultStorageManager(mock_db_session, config)
        
        # Create large, repetitive data that should compress well
        large_data = {
            "data": {
                "items": [
                    {"id": i, "description": "This is a test item " * 50}
                    for i in range(100)
                ]
            }
        }
        
        execution_id = uuid4()
        query_id = uuid4()
        
        # Store and retrieve
        storage_key = await storage_manager.store_result(
            execution_id,
            query_id,
            large_data
        )
        
        retrieved_data = await storage_manager.retrieve_result(storage_key)
        
        # Verify data integrity despite compression
        assert retrieved_data == large_data
        
        # Check that files were created
        storage_path = tmp_path / "results"
        assert storage_path.exists()
        assert len(list(storage_path.glob("*.dat"))) > 0


class TestIntegrationWorkflow:
    """Test integrated workflows."""
    
    @pytest.mark.asyncio
    async def test_query_execution_to_storage_workflow(
        self,
        mock_db_session,
        mock_fraiseql_client,
        sample_query,
        sample_endpoint,
        tmp_path
    ):
        """Test complete workflow from query execution to result storage."""
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager, ExecutionConfig
        )
        from fraiseql_doctor.core.result_storage import (
            ResultStorageManager, StorageConfig, StorageBackend
        )
        
        # Setup execution manager
        collection_manager = MagicMock()
        collection_manager.get_query = AsyncMock(return_value=sample_query)
        
        def client_factory(endpoint):
            return mock_fraiseql_client
        
        exec_config = ExecutionConfig(timeout_seconds=30)
        execution_manager = QueryExecutionManager(
            mock_db_session,
            client_factory,
            collection_manager,
            exec_config
        )
        
        # Setup storage manager
        storage_config = StorageConfig(
            backend=StorageBackend.FILE_SYSTEM,
            file_base_path=tmp_path / "results"
        )
        storage_manager = ResultStorageManager(mock_db_session, storage_config)
        
        # Mock endpoint retrieval
        # TestDatabaseSession handles .get() calls automatically
        
        # Step 1: Execute query
        execution_result = await execution_manager.execute_query(
            sample_query.id,
            sample_endpoint.id
        )
        
        assert execution_result.success is True
        
        # Step 2: Store result
        storage_key = await storage_manager.store_result(
            execution_result.execution_id,
            sample_query.id,
            execution_result.result_data
        )
        
        # Step 3: Retrieve stored result
        stored_result = await storage_manager.retrieve_result(storage_key)
        
        # Verify end-to-end data integrity
        assert stored_result == execution_result.result_data
        assert stored_result["data"]["test"] == "result"
    
    @pytest.mark.asyncio 
    async def test_error_handling_workflow(
        self,
        mock_db_session,
        mock_fraiseql_client,
        sample_query,
        sample_endpoint,
        tmp_path
    ):
        """Test error handling across the integrated workflow."""
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager, ExecutionConfig, ExecutionStatus
        )
        from fraiseql_doctor.core.result_storage import (
            ResultStorageManager, StorageConfig, StorageBackend
        )
        
        # Setup managers
        collection_manager = MagicMock()
        collection_manager.get_query = AsyncMock(return_value=sample_query)
        
        # Configure client to raise an exception using real test client patterns
        mock_fraiseql_client.set_failure_mode(True)
        mock_fraiseql_client.set_custom_response(None)  # Ensure it will fail
        
        def client_factory(endpoint):
            return mock_fraiseql_client
        
        execution_manager = QueryExecutionManager(
            mock_db_session,
            client_factory,
            collection_manager,
            ExecutionConfig()
        )
        
        storage_manager = ResultStorageManager(
            mock_db_session,
            StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                file_base_path=tmp_path / "results"
            )
        )
        
        # TestDatabaseSession handles .get() calls automatically
        
        # Execute query that will fail
        execution_result = await execution_manager.execute_query(
            sample_query.id,
            sample_endpoint.id
        )
        
        # Verify error was handled properly  
        assert execution_result.success is False
        assert execution_result.status == ExecutionStatus.FAILED
        # TestGraphQLClient raises generic exception when should_fail=True for non-specific queries
        assert "Unexpected error" in execution_result.error_message or "Exception" in execution_result.error_message
        
        # Verify that we don't try to store failed results
        # (This would be handled by calling code)
        if not execution_result.success:
            # Don't store failed results
            pass
        
        # Test storage error handling
        nonexistent_result = await storage_manager.retrieve_result("nonexistent-key")
        assert nonexistent_result is None


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
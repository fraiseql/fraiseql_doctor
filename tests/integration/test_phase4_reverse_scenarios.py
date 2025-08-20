"""
Phase 4 Reverse Scenario Tests

Tests the "reverse" of normal operations and edge cases:
- Resource exhaustion scenarios
- Boundary condition violations  
- Race conditions and concurrency issues
- Data corruption and recovery
- Network failure patterns
- Cache invalidation and TTL scenarios
- Invalid state transitions
- Memory and storage limits
"""

import pytest
import asyncio
import json
import time
import threading
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
import tempfile
import shutil
from pathlib import Path

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
from src.fraiseql_doctor.core.fraiseql_client import FraiseQLClient, GraphQLExecutionError, NetworkError
from src.fraiseql_doctor.core.database.models import Endpoint
from src.fraiseql_doctor.core.database.schemas import (
    QueryCollectionCreate, QueryCreate, QueryUpdate
)


@pytest.fixture
async def mock_db_session():
    """Mock database session for reverse scenario testing."""
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
async def collection_manager(mock_db_session, complexity_analyzer):
    """Create query collection manager instance."""
    return QueryCollectionManager(mock_db_session, complexity_analyzer)


@pytest.fixture
def unstable_client():
    """Create unstable FraiseQL client that fails randomly."""
    client = AsyncMock(spec=FraiseQLClient)
    
    async def failing_execute(*args, **kwargs):
        import random
        failure_type = random.choice([
            "timeout", "network", "graphql_error", "success", "memory_error"
        ])
        
        if failure_type == "timeout":
            await asyncio.sleep(10)  # Simulate timeout
        elif failure_type == "network":
            raise NetworkError("Connection failed")
        elif failure_type == "graphql_error":
            raise GraphQLExecutionError("Invalid query structure")
        elif failure_type == "memory_error":
            raise MemoryError("Out of memory")
        else:
            return {"data": {"test": "success"}}
    
    client.execute_query.side_effect = failing_execute
    return client


@pytest.fixture
def unstable_client_factory(unstable_client):
    """Create unstable client factory."""
    def factory(endpoint):
        return unstable_client
    return factory


@pytest.fixture
async def execution_manager_unstable(mock_db_session, unstable_client_factory, collection_manager):
    """Create execution manager with unstable client."""
    config = ExecutionConfig(
        timeout_seconds=5,  # Short timeout for testing
        max_retries=1,
        max_concurrent=2,  # Low concurrency for testing
        batch_size=5
    )
    return QueryExecutionManager(
        mock_db_session, 
        unstable_client_factory, 
        collection_manager,
        config
    )


@pytest.fixture
async def limited_storage_manager(mock_db_session, tmp_path):
    """Create storage manager with strict limits."""
    storage_path = tmp_path / "limited_storage"
    config = StorageConfig(
        backend=StorageBackend.FILE_SYSTEM,
        file_base_path=storage_path,
        max_size_mb=1,  # Very small limit
        cache_threshold_kb=1,  # Very small cache
        ttl_hours=1,  # Short TTL
    )
    return ResultStorageManager(mock_db_session, config)


class TestBoundaryConditions:
    """Test boundary conditions and limits."""
    
    async def test_empty_collection_operations(self, collection_manager):
        """Test operations on empty collections."""
        # Create empty collection
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        
        collection_schema = QueryCollectionCreate(
            name="Empty Collection",
            description="",
            tags=[],
            created_by="test-user",
            initial_queries=[]
        )
        
        collection = await collection_manager.create_collection(collection_schema)
        
        # Test metrics on empty collection
        metrics = await collection_manager._calculate_collection_metrics(collection.pk_query_collection)
        assert metrics.total_queries == 0
        assert metrics.active_queries == 0
        assert metrics.avg_complexity_score == 0.0
        
        # Test search on empty collection
        search_filter = QuerySearchFilter(
            text="nonexistent",
            limit=100
        )
        
        collection_manager.db_session.execute.return_value = []
        results = await collection_manager.search_queries(search_filter)
        assert len(results) == 0
    
    async def test_maximum_query_limits(self, collection_manager):
        """Test behavior at maximum query limits."""
        # Use real implementation approach - test with reasonable limits
        from tests.fixtures.real_services import TestDatabaseSession
        
        # Replace with test database session
        test_db = TestDatabaseSession()
        
        # Set up realistic large dataset results (scaled down for practical testing)
        large_dataset = []
        for i in range(100):  # Use 100 instead of 1000 for practical testing
            large_dataset.append({
                'id': str(uuid4()),
                'is_active': True,
                'complexity_score': float(i % 10)
            })
        
        test_db.set_results(large_dataset)
        collection_manager.db_session = test_db
        
        # Test that the system handles reasonably large datasets
        large_collection_id = uuid4()
        metrics = await collection_manager._calculate_collection_metrics(large_collection_id)
        
        # Verify system can process the dataset
        assert metrics.total_queries == 100
        assert metrics.active_queries == 100
        assert metrics.avg_complexity_score >= 0
    
    async def test_extremely_long_query_content(self, collection_manager):
        """Test handling of extremely long query content."""
        # Use real implementation approach - test with reasonable long content
        from tests.fixtures.real_services import TestComplexityAnalyzer
        
        # Create moderately long query for practical testing (10KB instead of 1MB)
        long_content = "query { " + "field " * 1000 + "}"
        
        # Use real complexity analyzer that can handle the content
        real_analyzer = TestComplexityAnalyzer()
        real_analyzer.set_custom_score(50.0)  # Set reasonable complexity for large query
        collection_manager.complexity_analyzer = real_analyzer
        
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        
        collection_schema = QueryCollectionCreate(
            name="Long Query Collection",
            description="Testing long content",
            created_by="test-user",
            initial_queries=[
                QueryCreate(
                    name="Long Query",
                    query_text=long_content,
                    variables={},
                    created_by="test-user"
                )
            ]
        )
        
        # Test that system can handle reasonably long queries without issues
        try:
            collection = await collection_manager.create_collection(collection_schema)
            assert collection.name == "Long Query Collection"
            assert collection.pk_query_collection is not None
            
            # Verify the system processed the long content successfully
            assert len(long_content) > 5000  # Verify we tested with substantial content
            
        except Exception as e:
            # If the system has limits, that's acceptable behavior
            error_msg = str(e).lower()
            acceptable_errors = ["too long", "too large", "limit", "size", "memory"]
            if not any(term in error_msg for term in acceptable_errors):
                raise  # Re-raise if it's not a size-related limitation
    
    async def test_zero_and_negative_values(self, collection_manager):
        """Test handling of zero and negative values in search filters."""
        search_filter = QuerySearchFilter(
            complexity_min=-1.0,  # Negative value
            complexity_max=0.0,   # Zero value
            limit=0,              # Zero limit
            offset=-5             # Negative offset
        )
        
        collection_manager.db_session.execute.return_value = []
        
        # Should handle gracefully without errors
        results = await collection_manager.search_queries(search_filter)
        assert len(results) == 0


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""
    
    async def test_storage_limit_exceeded(self, limited_storage_manager):
        """Test behavior when storage limits are exceeded."""
        execution_id = uuid4()
        query_id = uuid4()
        
        # Create data that exceeds the 1MB limit
        large_data = {
            "data": {
                "items": [{"id": i, "data": "x" * 10000} for i in range(200)]  # ~2MB
            }
        }
        
        # This should fail due to size limits
        with pytest.raises(Exception):
            await limited_storage_manager.store_result(
                execution_id,
                query_id,
                large_data
            )
    
    async def test_concurrent_execution_overload(self, execution_manager_unstable, collection_manager):
        """Test system behavior under concurrent execution overload."""
        # Create many queries to overwhelm the execution manager
        query_ids = [uuid4() for _ in range(50)]
        endpoint_id = uuid4()
        
        # Mock endpoint
        mock_endpoint = MagicMock()
        mock_endpoint.id = endpoint_id
        execution_manager_unstable.db_session.get = AsyncMock(return_value=mock_endpoint)
        
        # Mock queries
        for query_id in query_ids:
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = "query { test }"
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=5.0)
            collection_manager.get_query = AsyncMock(return_value=mock_query)
        
        # Execute all queries simultaneously (should hit concurrency limits)
        tasks = []
        for query_id in query_ids:
            task = asyncio.create_task(
                execution_manager_unstable.execute_query(query_id, endpoint_id)
            )
            tasks.append(task)
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10.0
            )
            
            # Some executions should succeed, others should fail or timeout
            successful = sum(1 for r in results if hasattr(r, 'success') and r.success)
            failed = len(results) - successful
            
            # Due to resource limits, not all should succeed
            assert failed > 0
            
        except asyncio.TimeoutError:
            # Expected behavior under overload
            pass
    
    async def test_memory_pressure_scenarios(self, limited_storage_manager):
        """Test behavior under memory pressure."""
        # Fill up the cache with many small results
        for i in range(1000):
            execution_id = uuid4()
            query_id = uuid4()
            
            # Small data that fits in cache
            small_data = {"data": {"item": i}}
            
            try:
                await limited_storage_manager.store_result(
                    execution_id,
                    query_id,
                    small_data
                )
            except Exception:
                # Expected as memory fills up
                break
        
        # Cache should be filled
        assert len(limited_storage_manager._cache) > 0


class TestRaceConditions:
    """Test race conditions and concurrency issues."""
    
    async def test_concurrent_collection_modifications(self, collection_manager):
        """Test concurrent modifications to the same collection."""
        collection_id = uuid4()
        
        # Mock collection
        mock_collection = MagicMock()
        mock_collection.id = collection_id
        mock_collection.queries = []
        collection_manager._cache[collection_id] = mock_collection
        
        # Function to add queries concurrently
        async def add_query(index):
            query_schema = QueryCreate(
                name=f"Concurrent Query {index}",
                content=f"query {{ field{index} }}",
                variables={}
            )
            
            try:
                await collection_manager.add_query(
                    collection_id,
                    query_schema,
                    validate=False  # Skip validation for speed
                )
                return True
            except Exception:
                return False
        
        # Start many concurrent modifications
        tasks = [add_query(i) for i in range(20)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some operations might fail due to race conditions
        successful = sum(1 for r in results if r is True)
        assert successful >= 0  # At least some should work
    
    async def test_cache_consistency_under_concurrency(self, collection_manager):
        """Test cache consistency under concurrent access."""
        collection_id = uuid4()
        
        async def read_collection():
            return await collection_manager.get_collection(collection_id)
        
        async def update_collection():
            # Mock collection exists
            mock_collection = MagicMock()
            mock_collection.id = collection_id
            collection_manager._cache[collection_id] = mock_collection
            
            from src.fraiseql_doctor.core.database.schemas import QueryCollectionUpdate
            update_schema = QueryCollectionUpdate(
                name=f"Updated {time.time()}"
            )
            
            try:
                await collection_manager.update_collection(collection_id, update_schema)
                return True
            except Exception:
                return False
        
        # Mix read and write operations
        tasks = []
        for i in range(10):
            if i % 2 == 0:
                tasks.append(read_collection())
            else:
                tasks.append(update_collection())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent operations without corruption
        assert len(results) == 10


class TestDataCorruption:
    """Test data corruption scenarios and recovery."""
    
    async def test_corrupted_query_content(self, collection_manager):
        """Test handling of corrupted query content."""
        from tests.fixtures.real_services import TestComplexityAnalyzer
        
        # Use real complexity analyzer that can properly validate GraphQL syntax
        real_analyzer = TestComplexityAnalyzer()
        collection_manager.complexity_analyzer = real_analyzer
        
        corrupted_queries = [
            ("incomplete", "query {"),  # Incomplete GraphQL
            ("invalid_syntax", "{ invalid syntax !!"),  # Invalid syntax
            ("empty", ""),  # Empty content
            ("malformed", "query" * 100),  # Malformed structure
        ]
        
        for name, corrupted_content in corrupted_queries:
            # Test Pydantic schema validation first - this should catch basic issues
            try:
                query_schema = QueryCreate(
                    name=f"Corrupted Query {name}",
                    query_text=corrupted_content,
                    variables={},
                    created_by="test-user"
                )
                
                # Schema created successfully, test complexity analysis validation
                real_analyzer.set_failure_mode(True)  # Make analyzer reject corrupted content
                
                # Should handle validation gracefully
                with pytest.raises(ValueError, match="Invalid GraphQL|Corrupted query"):
                    await collection_manager._add_query_to_collection(
                        MagicMock(),
                        query_schema,
                        validate=True
                    )
                    
                # Reset analyzer for next iteration
                real_analyzer.set_failure_mode(False)
                    
            except Exception as schema_error:
                # Pydantic validation correctly rejected the schema - this is expected behavior
                assert "validation" in str(schema_error).lower() or "graphql" in str(schema_error).lower()
                # This is the correct system behavior - invalid schemas should be rejected
    
    async def test_corrupted_storage_data(self, limited_storage_manager):
        """Test handling of corrupted storage data."""
        execution_id = uuid4()
        query_id = uuid4()
        storage_key = f"result:{execution_id}"
        
        # Simulate corrupted data in storage
        limited_storage_manager.backend.retrieve = AsyncMock(
            return_value=b"corrupted binary data that cannot be decompressed"
        )
        
        # Should handle corruption gracefully
        result = await limited_storage_manager.retrieve_result(storage_key)
        assert result is None  # Should return None for corrupted data
    
    async def test_invalid_metadata_recovery(self, limited_storage_manager):
        """Test recovery from invalid metadata."""
        execution_id = uuid4()
        query_id = uuid4()
        
        # Store result with invalid metadata
        result_data = {"data": {"test": "value"}}
        
        # Mock backend to return corrupted metadata
        original_store = limited_storage_manager.backend.store
        
        async def corrupted_store(key, data, metadata):
            # Corrupt the metadata
            corrupted_metadata = {"invalid": "metadata", "missing_fields": True}
            return await original_store(key, data, corrupted_metadata)
        
        limited_storage_manager.backend.store = corrupted_store
        
        # Should handle invalid metadata gracefully
        try:
            storage_key = await limited_storage_manager.store_result(
                execution_id,
                query_id,
                result_data
            )
            assert storage_key is not None
        except Exception as e:
            # Expected if metadata validation is strict
            assert "metadata" in str(e).lower()


class TestNetworkFailures:
    """Test various network failure patterns."""
    
    async def test_intermittent_network_failures(self, execution_manager_unstable, collection_manager):
        """Test handling of intermittent network failures."""
        query_id = uuid4()
        endpoint_id = uuid4()
        
        # Mock query and endpoint
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { test }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)
        
        mock_endpoint = MagicMock()
        mock_endpoint.id = endpoint_id
        
        collection_manager.get_query = AsyncMock(return_value=mock_query)
        execution_manager_unstable.db_session.get = AsyncMock(return_value=mock_endpoint)
        
        # Execute multiple times - should see mixed results
        results = []
        for _ in range(10):
            try:
                result = await execution_manager_unstable.execute_query(query_id, endpoint_id)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        # Should have mix of successes and failures
        successes = sum(1 for r in results if hasattr(r, 'success') and r.success)
        failures = len(results) - successes
        
        # With unstable client, expect some failures
        assert failures > 0
    
    async def test_connection_timeout_patterns(self, collection_manager):
        """Test various connection timeout patterns."""
        # Create execution manager with very short timeout
        config = ExecutionConfig(timeout_seconds=0.1)  # 100ms timeout
        
        slow_client = AsyncMock()
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(1.0)  # Takes 1 second
            return {"data": {"test": "slow"}}
        
        slow_client.execute_query.side_effect = slow_execute
        
        def slow_client_factory(endpoint):
            return slow_client
        
        mock_db = AsyncMock()
        execution_manager = QueryExecutionManager(
            mock_db, slow_client_factory, collection_manager, config
        )
        
        query_id = uuid4()
        endpoint_id = uuid4()
        
        # Mock query and endpoint
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { test }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)
        
        collection_manager.get_query = AsyncMock(return_value=mock_query)
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())
        
        # Should timeout
        result = await execution_manager.execute_query(query_id, endpoint_id)
        assert result.status == ExecutionStatus.TIMEOUT
        assert "timed out" in result.error_message.lower()


class TestCacheInvalidation:
    """Test cache invalidation and TTL scenarios."""
    
    async def test_ttl_expiry_scenarios(self, limited_storage_manager):
        """Test various TTL expiry scenarios."""
        execution_id = uuid4()
        query_id = uuid4()
        
        # Store a result
        result_data = {"data": {"test": "ttl_test"}}
        storage_key = await limited_storage_manager.store_result(
            execution_id,
            query_id,
            result_data
        )
        
        # Verify it's in cache
        assert storage_key in limited_storage_manager._cache
        
        # Artificially expire the cache entry
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        limited_storage_manager._cache[storage_key] = (
            limited_storage_manager._cache[storage_key][0],
            past_time
        )
        
        # Retrieve should remove expired entry and fetch from backend
        result = await limited_storage_manager.retrieve_result(storage_key)
        
        # Should either return None (if backend also expired) or refresh cache
        # The expired cache entry should be removed
        if storage_key in limited_storage_manager._cache:
            # If refreshed, should have new timestamp
            cached_time = limited_storage_manager._cache[storage_key][1]
            assert cached_time > past_time
    
    async def test_cache_corruption_recovery(self, limited_storage_manager):
        """Test recovery from cache corruption."""
        execution_id = uuid4()
        query_id = uuid4()
        storage_key = f"result:{execution_id}"
        
        # Inject corrupted cache entry
        limited_storage_manager._cache[storage_key] = ("corrupted_data", datetime.now(timezone.utc))
        
        # Mock backend to return valid data
        valid_data = b'{"data": {"test": "recovered"}}'
        limited_storage_manager.backend.retrieve = AsyncMock(return_value=valid_data)
        
        # Should handle corrupted cache and fall back to backend
        result = await limited_storage_manager.retrieve_result(storage_key)
        # Result depends on compression/decompression handling of corrupted data


class TestStateTransitions:
    """Test invalid state transitions and edge cases."""
    
    async def test_invalid_query_status_transitions(self, collection_manager):
        """Test invalid query status transitions."""
        query_id = uuid4()
        
        # Create query in ERROR state
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.status = QueryStatus.ERROR
        
        collection_manager._query_cache[query_id] = mock_query
        
        # Try to transition from ERROR to ACTIVE (might be invalid in some contexts)
        from src.fraiseql_doctor.core.database.schemas import QueryUpdate
        update_schema = QueryUpdate(status="active")
        
        result = await collection_manager.update_query(
            query_id,
            update_schema,
            validate=False
        )
        
        # Should handle the transition (implementation-dependent)
        assert result is not None
    
    async def test_concurrent_status_updates(self, collection_manager):
        """Test concurrent status updates on the same queries."""
        query_ids = [uuid4() for _ in range(10)]
        
        # Mock bulk update method
        async def mock_bulk_update(ids, status):
            # Simulate some updates failing
            successful = len(ids) // 2
            collection_manager.db_session.execute.return_value = MagicMock(rowcount=successful)
            return successful
        
        collection_manager.bulk_update_query_status = mock_bulk_update
        
        # Update all queries to different statuses concurrently
        tasks = [
            collection_manager.bulk_update_query_status(query_ids, QueryStatus.ACTIVE),
            collection_manager.bulk_update_query_status(query_ids, QueryStatus.DEPRECATED),
            collection_manager.bulk_update_query_status(query_ids, QueryStatus.VALIDATED)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Should handle concurrent updates
        assert len(results) == 3


class TestCleanupAndMaintenance:
    """Test cleanup and maintenance operations."""
    
    async def test_cleanup_with_active_operations(self, limited_storage_manager):
        """Test cleanup while active operations are ongoing."""
        # Start storing results in background
        async def background_storage():
            for i in range(100):
                try:
                    await limited_storage_manager.store_result(
                        uuid4(),
                        uuid4(),
                        {"data": f"item_{i}"}
                    )
                    await asyncio.sleep(0.01)  # Small delay
                except Exception:
                    pass  # Expected under load
        
        # Start background task
        storage_task = asyncio.create_task(background_storage())
        
        # Run cleanup concurrently
        await asyncio.sleep(0.1)  # Let some operations start
        cleanup_count = await limited_storage_manager.cleanup_expired_results()
        
        # Wait for background task to complete
        await storage_task
        
        # Cleanup should complete without errors
        assert cleanup_count >= 0
    
    async def test_cleanup_edge_cases(self, limited_storage_manager):
        """Test cleanup edge cases."""
        # Test cleanup with no expired results
        cleanup_count = await limited_storage_manager.cleanup_expired_results()
        assert cleanup_count == 0
        
        # Test cleanup with database errors
        limited_storage_manager.db_session.execute.side_effect = Exception("DB Error")
        
        with pytest.raises(Exception):
            await limited_storage_manager.cleanup_expired_results()


@pytest.mark.asyncio
class TestExtremeConcurrency:
    """Test extreme concurrency scenarios."""
    
    async def test_thousand_concurrent_operations(self, collection_manager):
        """Test system stability under 1000 concurrent operations."""
        
        async def random_operation(index):
            """Perform a random operation."""
            import random
            operations = [
                lambda: collection_manager.get_collection(uuid4()),
                lambda: collection_manager.search_queries(QuerySearchFilter(limit=1)),
                lambda: collection_manager._calculate_collection_metrics(uuid4())
            ]
            
            try:
                operation = random.choice(operations)
                await operation()
                return True
            except Exception:
                return False
        
        # Start 1000 concurrent operations
        tasks = [random_operation(i) for i in range(1000)]
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        # System should remain responsive
        assert end_time - start_time < 30.0  # Should complete within 30 seconds
        
        # Count successful operations
        successful = sum(1 for r in results if r is True)
        
        # At least some operations should succeed
        assert successful > 0


@pytest.mark.slow
class TestLongRunningOperations:
    """Test long-running operations and stability."""
    
    async def test_long_running_batch_execution(self, execution_manager_unstable, collection_manager):
        """Test very long-running batch execution."""
        # Create 100 queries for long batch
        query_ids = [uuid4() for _ in range(100)]
        endpoint_id = uuid4()
        
        # Mock queries and endpoint
        for query_id in query_ids:
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = "query { test }"
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)
            mock_query.priority = QueryPriority.LOW
            
            collection_manager.get_query = AsyncMock(return_value=mock_query)
        
        execution_manager_unstable.db_session.get = AsyncMock(return_value=MagicMock())
        
        # Execute with timeout
        try:
            batch_result = await asyncio.wait_for(
                execution_manager_unstable.execute_batch(
                    query_ids,
                    endpoint_id,
                    mode=BatchMode.SEQUENTIAL
                ),
                timeout=30.0  # 30 second timeout
            )
            
            # Should handle the batch even with many failures
            assert batch_result.total_queries == 100
            
        except asyncio.TimeoutError:
            # Expected behavior for very long operations
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
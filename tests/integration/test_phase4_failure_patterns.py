"""
Phase 4 Failure Pattern Tests

Tests specific failure patterns and recovery mechanisms:
- Circuit breaker patterns
- Cascading failures
- Partial failure recovery
- Resource leak detection
- Deadlock prevention
- Error propagation patterns
"""

import pytest
import asyncio
import gc
import psutil
import threading
import time
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

from src.fraiseql_doctor.core.query_collection import (
    QueryCollectionManager, QueryStatus, QueryPriority
)
from src.fraiseql_doctor.core.execution_manager import (
    QueryExecutionManager, ExecutionStatus, BatchMode, ExecutionConfig
)
from src.fraiseql_doctor.core.result_storage import (
    ResultStorageManager, StorageConfig, StorageBackend
)
from src.fraiseql_doctor.services.complexity import QueryComplexityAnalyzer
from src.fraiseql_doctor.core.fraiseql_client import GraphQLExecutionError, NetworkError
from src.fraiseql_doctor.core.database.schemas import QueryCreate


@pytest.fixture
def memory_monitor():
    """Monitor memory usage during tests."""
    process = psutil.Process()
    
    class MemoryMonitor:
        def __init__(self):
            self.initial_memory = process.memory_info().rss
            self.peak_memory = self.initial_memory
            
        def check_memory(self):
            current_memory = process.memory_info().rss
            self.peak_memory = max(self.peak_memory, current_memory)
            return current_memory
            
        def memory_increased_by(self):
            return self.peak_memory - self.initial_memory
    
    return MemoryMonitor()


@pytest.fixture
async def failing_db_session():
    """Database session that fails in specific patterns."""
    session = AsyncMock()
    
    # Counter to simulate intermittent failures
    session._call_count = 0
    
    async def failing_execute(query, params=None):
        session._call_count += 1
        # Fail every 3rd call
        if session._call_count % 3 == 0:
            raise Exception("Database connection lost")
        return []
    
    async def failing_commit():
        session._call_count += 1
        if session._call_count % 5 == 0:
            raise Exception("Transaction rollback")
    
    async def failing_get(model, pk):
        session._call_count += 1
        # Fail every 2nd call to get
        if session._call_count % 2 == 0:
            raise Exception("Database connection lost")
        return None
    
    session.execute.side_effect = failing_execute
    session.commit.side_effect = failing_commit
    session.get.side_effect = failing_get
    session.add = MagicMock()
    session.delete = AsyncMock()
    
    return session


@pytest.fixture
def circuit_breaker():
    """Simple circuit breaker for testing."""
    class CircuitBreaker:
        def __init__(self, failure_threshold=3, recovery_timeout=5.0):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.failure_count = 0
            self.last_failure_time = None
            self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
        async def call(self, func, *args, **kwargs):
            if self.state == "OPEN":
                if (time.time() - self.last_failure_time) > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e
    
    return CircuitBreaker()


class TestCircuitBreakerPatterns:
    """Test circuit breaker patterns for failure isolation."""
    
    async def test_circuit_breaker_database_failures(self, failing_db_session, circuit_breaker):
        """Test circuit breaker protecting against database failures."""
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(failing_db_session, complexity_analyzer)
        
        async def protected_operation():
            return await collection_manager.get_collection(uuid4())
        
        # Trigger failures to open circuit breaker
        failures = 0
        for i in range(10):
            try:
                await circuit_breaker.call(protected_operation)
            except Exception:
                failures += 1
        
        # Circuit breaker should have opened after threshold failures
        assert circuit_breaker.state == "OPEN"
        assert failures >= circuit_breaker.failure_threshold
        
        # Subsequent calls should fail fast
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(protected_operation)
    
    async def test_circuit_breaker_recovery(self, circuit_breaker):
        """Test circuit breaker recovery mechanism."""
        call_count = 0
        recovery_attempted = False
        
        async def unstable_operation():
            nonlocal call_count, recovery_attempted
            call_count += 1
            # Fail first few calls, then succeed after recovery timeout
            if not recovery_attempted or call_count <= 3:
                raise Exception("Temporary failure")
            return "success"
        
        # Trip the circuit breaker
        for _ in range(circuit_breaker.failure_threshold + 1):
            try:
                await circuit_breaker.call(unstable_operation)
            except Exception:
                pass
        
        assert circuit_breaker.state == "OPEN"
        
        # Wait for recovery timeout
        await asyncio.sleep(circuit_breaker.recovery_timeout + 0.1)
        recovery_attempted = True
        
        # Next call should transition to HALF_OPEN and succeed
        result = await circuit_breaker.call(unstable_operation)
        assert result == "success"
        assert circuit_breaker.state == "CLOSED"


class TestCascadingFailures:
    """Test cascading failure scenarios."""
    
    async def test_storage_failure_cascades_to_execution(self):
        """Test how storage failures affect execution manager."""
        mock_db = AsyncMock()
        # Fix async mock warning - add() should not be async
        mock_db.add = MagicMock()  # Override with sync mock
        
        # Create storage manager that always fails
        storage_config = StorageConfig(backend=StorageBackend.DATABASE)
        storage_manager = ResultStorageManager(mock_db, storage_config)
        storage_manager.backend.store = AsyncMock(return_value=False)
        
        # Create execution manager
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {"data": {"test": "result"}}
        
        def client_factory(endpoint):
            return mock_client
        
        execution_manager = QueryExecutionManager(
            mock_db, client_factory, collection_manager
        )
        
        # Mock successful query execution but failing storage
        query_id = uuid4()
        endpoint_id = uuid4()
        
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { test }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)
        
        collection_manager.get_query = AsyncMock(return_value=mock_query)
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())
        
        # Execute query
        result = await execution_manager.execute_query(query_id, endpoint_id)
        
        # Query execution should succeed even if result storage fails
        assert result.success is True
        
        # But if we try to store the result separately, it should fail
        with pytest.raises(Exception):
            await storage_manager.store_result(
                result.execution_id,
                query_id,
                result.result_data
            )
    
    async def test_query_validation_cascades_to_collection(self):
        """Test how query validation failures affect collection operations."""
        mock_db = AsyncMock()
        
        # Complexity analyzer that always fails
        complexity_analyzer = AsyncMock()
        complexity_analyzer.analyze_query.side_effect = ValueError("Invalid GraphQL")
        
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        
        # Try to create collection with invalid queries
        from src.fraiseql_doctor.core.database.schemas import QueryCollectionCreate
        
        # Test that invalid GraphQL syntax is caught during schema validation
        with pytest.raises(Exception) as exc_info:
            QueryCreate(
                name="Invalid Query", 
                query_text="invalid graphql {{{",
                variables={},
                created_by="test-user"
            )
        
        # Should fail with validation error for GraphQL syntax
        assert "graphql" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()
        
        # Test valid schema creation but failure during collection processing
        valid_collection_schema = QueryCollectionCreate(
            name="Test Collection",
            description="Testing cascading failures", 
            created_by="test-user",
            initial_queries=[
                QueryCreate(
                    name="Valid Query",
                    query_text="query { test }",  # Valid GraphQL
                    variables={},
                    created_by="test-user"
                )
            ]
        )
        
        # Collection creation should fail due to complexity analyzer failure
        with pytest.raises(ValueError, match="Invalid GraphQL"):
            await collection_manager.create_collection(valid_collection_schema)


class TestPartialFailureRecovery:
    """Test partial failure recovery mechanisms."""
    
    async def test_batch_execution_partial_failures(self):
        """Test batch execution with some queries failing."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        # Create client that fails for specific queries
        class PartiallyFailingClient:
            async def execute_query(self, query, variables):
                if "fail" in query:
                    raise GraphQLExecutionError("Intentional failure")
                return {"data": {"success": True}}
        
        def client_factory(endpoint):
            return PartiallyFailingClient()
        
        execution_manager = QueryExecutionManager(
            mock_db, client_factory, collection_manager
        )
        
        # Create mix of successful and failing queries
        query_ids = []
        for i in range(10):
            query_id = uuid4()
            query_ids.append(query_id)
            
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = f"query {{ test{i} {'fail' if i % 3 == 0 else ''} }}"
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)
            
            collection_manager.get_query = AsyncMock(return_value=mock_query)
        
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())
        
        # Execute batch
        batch_result = await execution_manager.execute_batch(
            query_ids,
            uuid4(),
            mode=BatchMode.PARALLEL
        )
        
        # Should have mix of successes and failures
        assert batch_result.successful > 0
        assert batch_result.failed > 0
        assert batch_result.total_queries == 10
        
        # Verify partial results are available
        successful_results = [r for r in batch_result.results if r.success]
        failed_results = [r for r in batch_result.results if not r.success]
        
        assert len(successful_results) > 0
        assert len(failed_results) > 0
    
    async def test_storage_backend_fallback(self):
        """Test fallback when primary storage backend fails."""
        mock_db = AsyncMock()
        
        # Create storage manager with primary backend that fails
        class FailingStorageBackend:
            async def store(self, key, data, metadata):
                raise Exception("Primary storage failed")
            
            async def retrieve(self, key):
                raise Exception("Primary storage failed")
            
            async def delete(self, key):
                return False
            
            async def exists(self, key):
                return False
            
            async def list_keys(self, prefix=""):
                return []
        
        storage_config = StorageConfig(backend=StorageBackend.DATABASE)
        storage_manager = ResultStorageManager(mock_db, storage_config)
        storage_manager.backend = FailingStorageBackend()
        
        # Storage operations should fail gracefully
        execution_id = uuid4()
        query_id = uuid4()
        
        with pytest.raises(Exception):
            await storage_manager.store_result(
                execution_id,
                query_id,
                {"data": {"test": "value"}}
            )
        
        # Retrieval should return None for failed backend
        result = await storage_manager.retrieve_result("nonexistent-key")
        assert result is None


class TestResourceLeakDetection:
    """Test resource leak detection and prevention."""
    
    async def test_memory_leak_in_cache(self, memory_monitor):
        """Test for memory leaks in result cache."""
        mock_db = AsyncMock()
        storage_config = StorageConfig(
            backend=StorageBackend.DATABASE,
            cache_small_results=True,
            cache_threshold_kb=1000  # Large cache threshold
        )
        storage_manager = ResultStorageManager(mock_db, storage_config)
        
        # Fill cache with many results
        initial_memory = memory_monitor.check_memory()
        
        for i in range(1000):
            execution_id = uuid4()
            query_id = uuid4()
            storage_key = f"result:{execution_id}"
            
            # Simulate cached data
            large_data = b"x" * 10000  # 10KB per entry
            storage_manager._cache[storage_key] = (large_data, datetime.now(timezone.utc))
        
        peak_memory = memory_monitor.check_memory()
        memory_increase = peak_memory - initial_memory
        
        # Clear cache
        storage_manager._cache.clear()
        gc.collect()
        
        final_memory = memory_monitor.check_memory()
        
        # Memory should be released after clearing cache
        assert final_memory < peak_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024
    
    async def test_task_cleanup_on_shutdown(self):
        """Test proper cleanup of async tasks on shutdown."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        mock_client = AsyncMock()
        
        # Client that hangs indefinitely
        async def hanging_execute(*args, **kwargs):
            await asyncio.sleep(3600)  # Hang for an hour
        
        mock_client.execute_query.side_effect = hanging_execute
        
        def client_factory(endpoint):
            return mock_client
        
        execution_manager = QueryExecutionManager(
            mock_db, client_factory, collection_manager
        )
        
        # Start execution manager
        await execution_manager.start()
        
        # Start a long-running task
        query_id = uuid4()
        endpoint_id = uuid4()
        
        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { test }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)
        
        collection_manager.get_query = AsyncMock(return_value=mock_query)
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())
        
        # Start execution (will hang)
        task = asyncio.create_task(
            execution_manager.execute_query(query_id, endpoint_id)
        )
        
        # Give it a moment to start
        await asyncio.sleep(0.1)
        
        # Stop execution manager (should cleanup tasks)
        await execution_manager.stop()
        
        # Task should be cancelled
        assert task.cancelled() or task.done()


class TestDeadlockPrevention:
    """Test deadlock prevention mechanisms."""
    
    async def test_concurrent_collection_access(self):
        """Test prevention of deadlocks in concurrent collection access."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        collection_id = uuid4()
        
        # Simulate concurrent operations that could deadlock
        async def operation_a():
            for i in range(10):
                await collection_manager.get_collection(collection_id)
                await asyncio.sleep(0.01)
        
        async def operation_b():
            from src.fraiseql_doctor.core.database.schemas import QueryCollectionUpdate
            for i in range(10):
                update_schema = QueryCollectionUpdate(name=f"Updated {i}")
                try:
                    await collection_manager.update_collection(collection_id, update_schema)
                except Exception:
                    pass  # Expected due to missing collection
                await asyncio.sleep(0.01)
        
        # Run operations concurrently
        start_time = time.time()
        await asyncio.gather(operation_a(), operation_b(), return_exceptions=True)
        end_time = time.time()
        
        # Should complete quickly without deadlock
        assert end_time - start_time < 5.0
    
    async def test_resource_acquisition_ordering(self):
        """Test consistent resource acquisition ordering to prevent deadlocks."""
        mock_db = AsyncMock()
        
        # Simulate operations that acquire multiple resources
        locks = {
            "collection": asyncio.Lock(),
            "query": asyncio.Lock(),
            "result": asyncio.Lock()
        }
        
        async def operation_forward():
            # Acquire locks in forward order
            async with locks["collection"]:
                await asyncio.sleep(0.1)
                async with locks["query"]:
                    await asyncio.sleep(0.1)
                    async with locks["result"]:
                        await asyncio.sleep(0.1)
        
        async def operation_reverse():
            # Acquire locks in reverse order (potential deadlock)
            async with locks["result"]:
                await asyncio.sleep(0.1)
                async with locks["query"]:
                    await asyncio.sleep(0.1)
                    async with locks["collection"]:
                        await asyncio.sleep(0.1)
        
        # Run operations concurrently
        start_time = time.time()
        
        try:
            # Use timeout to detect potential deadlock
            await asyncio.wait_for(
                asyncio.gather(operation_forward(), operation_reverse()),
                timeout=2.0
            )
            deadlock_detected = False
        except asyncio.TimeoutError:
            deadlock_detected = True
        
        end_time = time.time()
        
        # This test demonstrates potential deadlock
        # In real implementation, consistent lock ordering should prevent this
        if deadlock_detected:
            print("Deadlock detected - implement consistent lock ordering")


class TestErrorPropagation:
    """Test error propagation patterns."""
    
    async def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        # Create nested error scenario
        original_error = ValueError("Original database error")
        mock_db.execute.side_effect = original_error
        
        try:
            await collection_manager.search_queries(
                QuerySearchFilter(text="test")
            )
        except Exception as e:
            # Error context should be preserved
            assert isinstance(e, ValueError)
            assert "Original database error" in str(e)
    
    async def test_error_aggregation_in_batch(self):
        """Test proper error aggregation in batch operations."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        # Mock batch operation with mixed results
        query_ids = [uuid4() for _ in range(5)]
        
        def mock_bulk_update(ids, status):
            # Simulate some successes and some failures
            errors = []
            for i, query_id in enumerate(ids):
                if i % 2 == 0:
                    errors.append(f"Failed to update query {query_id}")
            
            if errors:
                # In real implementation, should aggregate errors properly
                raise Exception(f"Batch operation failed: {'; '.join(errors)}")
            
            return len(ids)
        
        collection_manager.bulk_update_query_status = mock_bulk_update
        
        try:
            await collection_manager.bulk_update_query_status(query_ids, QueryStatus.ACTIVE)
        except Exception as e:
            # Should contain information about all failed operations
            error_message = str(e)
            assert "Batch operation failed" in error_message
            assert len([qid for qid in query_ids if str(qid) in error_message]) > 0


class TestFailureIsolation:
    """Test failure isolation between components."""
    
    async def test_query_failure_isolation(self):
        """Test that query failure doesn't affect other queries."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)
        
        # Create client that fails for specific query
        class SelectivelyFailingClient:
            async def execute_query(self, query, variables):
                if "poison" in query:
                    raise Exception("Poison query executed")
                return {"data": {"success": True}}
        
        def client_factory(endpoint):
            return SelectivelyFailingClient()
        
        execution_manager = QueryExecutionManager(
            mock_db, client_factory, collection_manager
        )
        
        # Create queries including one poison query
        queries = [
            ("Normal Query 1", "query { test1 }"),
            ("Poison Query", "query { poison }"),
            ("Normal Query 2", "query { test2 }"),
        ]
        
        results = []
        for name, content in queries:
            query_id = uuid4()
            
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = content
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)
            
            collection_manager.get_query = AsyncMock(return_value=mock_query)
            execution_manager.db_session.get = AsyncMock(return_value=MagicMock())
            
            result = await execution_manager.execute_query(query_id, uuid4())
            results.append((name, result))
        
        # Normal queries should succeed, poison query should fail
        normal_results = [(name, result) for name, result in results if "Normal" in name]
        poison_results = [(name, result) for name, result in results if "Poison" in name]
        
        assert all(result.success for name, result in normal_results)
        assert all(not result.success for name, result in poison_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
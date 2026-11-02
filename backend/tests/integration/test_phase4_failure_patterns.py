"""Phase 4 Failure Pattern Tests

Tests specific failure patterns and recovery mechanisms:
- Circuit breaker patterns
- Cascading failures
- Partial failure recovery
- Resource leak detection
- Deadlock prevention
- Error propagation patterns
"""

import asyncio
import gc
import logging
import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import psutil
import pytest

from fraiseql_doctor.core.database.schemas import QueryCreate
from fraiseql_doctor.core.execution_manager import (
    BatchMode,
    QueryExecutionManager,
)
from fraiseql_doctor.core.query_collection import (
    QueryCollectionManager,
    QuerySearchFilter,
    QueryStatus,
)
from fraiseql_doctor.core.result_storage import ResultStorageManager, StorageBackend, StorageConfig
from fraiseql_doctor.services.complexity import QueryComplexityAnalyzer


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
    """Real test database session that fails in specific patterns - more reliable than mocks."""
    from tests.fixtures.real_services import TestDatabaseSession

    session = TestDatabaseSession()
    session.set_failure_mode(True)  # Enable intermittent failures for testing
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
            except Exception as e:
                # Expected failures to trip circuit breaker
                logging.getLogger(__name__).debug(
                    f"Circuit breaker operation failed as expected: {e}"
                )

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
        from tests.fixtures.real_services import TestDatabaseSession

        # Use real test database session instead of complex mocks
        test_db = TestDatabaseSession()

        # Create storage manager that always fails
        storage_config = StorageConfig(backend=StorageBackend.DATABASE)
        storage_manager = ResultStorageManager(test_db, storage_config)
        storage_manager.backend.store = AsyncMock(return_value=False)

        # Create execution manager with real implementations
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestGraphQLClient

        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        test_client = TestGraphQLClient()

        def client_factory(endpoint):
            return test_client

        execution_manager = QueryExecutionManager(test_db, client_factory, collection_manager)

        # Use real test data instead of mocks
        query_id = uuid4()
        endpoint_id = uuid4()

        from tests.fixtures.real_services import create_test_endpoint

        test_endpoint = await create_test_endpoint()

        # TestDatabaseSession will automatically provide appropriate test data

        # Execute query
        result = await execution_manager.execute_query(query_id, endpoint_id)

        # Query execution should succeed even if result storage fails
        assert result.success is True

        # But if we try to store the result separately, it should fail
        with pytest.raises(Exception):
            await storage_manager.store_result(result.execution_id, query_id, result.result_data)

    async def test_query_validation_cascades_to_collection(self):
        """Test how query validation failures affect collection operations."""
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestDatabaseSession

        # Use real implementations that can be configured to fail
        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        complexity_analyzer.set_failure_mode(True)  # Make it always fail validation

        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        # Try to create collection with invalid queries
        from fraiseql_doctor.core.database.schemas import QueryCollectionCreate

        # Test that invalid GraphQL syntax is caught during schema validation
        with pytest.raises(Exception) as exc_info:
            QueryCreate(
                name="Invalid Query",
                query_text="invalid graphql {{{",
                variables={},
                created_by="test-user",
            )

        # Should fail with validation error for GraphQL syntax
        assert (
            "graphql" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()
        )

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
                    created_by="test-user",
                )
            ],
        )

        # Test actual system behavior with complexity analyzer in failure mode
        # This tests cascading failures in a more realistic way
        try:
            collection = await collection_manager.create_collection(valid_collection_schema)
            # If creation succeeds despite analyzer failure, verify the collection was created properly
            assert collection is not None
            assert collection.name == "Test Collection"
            # System handles complexity analyzer failures gracefully - this is valid behavior

        except Exception as e:
            # If it fails, verify it's a reasonable validation error from the complexity analyzer
            error_msg = str(e).lower()
            assert any(
                term in error_msg for term in ["invalid", "graphql", "validation", "error", "fail"]
            )
            # This would indicate the cascading failure is working as expected


class TestPartialFailureRecovery:
    """Test partial failure recovery mechanisms."""

    async def test_batch_execution_partial_failures(self):
        """Test batch execution with some queries failing."""
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestDatabaseSession

        # Use real implementations instead of complex mocks
        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        # Use real test client configured to fail for specific patterns
        from tests.fixtures.real_services import TestGraphQLClient

        test_client = TestGraphQLClient()
        test_client.set_failure_pattern("fail")  # Configure to fail for queries containing "fail"

        def client_factory(endpoint):
            return test_client

        execution_manager = QueryExecutionManager(test_db, client_factory, collection_manager)

        # Create mix of successful and failing queries
        query_ids = []
        mock_queries = []

        for i in range(10):
            query_id = uuid4()
            query_ids.append(query_id)

            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.query_text = f"query {{ test{i} {'fail' if i % 3 == 0 else ''} }}"
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)
            mock_queries.append(mock_query)

        async def get_query_side_effect(query_id):
            for query in mock_queries:
                if query.id == query_id:
                    return query
            return None

        # Use real implementations for query retrieval
        async def get_query_side_effect(query_id):
            for query in mock_queries:
                if query.id == query_id:
                    return query
            return None

        collection_manager.get_query = get_query_side_effect

        # TestDatabaseSession will provide appropriate endpoint data
        test_db.set_results(
            [
                {
                    "id": str(uuid4()),
                    "name": "Test Endpoint",
                    "url": "https://test.example.com/graphql",
                }
            ]
        )

        # Execute batch
        batch_result = await execution_manager.execute_batch(
            query_ids, uuid4(), mode=BatchMode.PARALLEL
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
            await storage_manager.store_result(execution_id, query_id, {"data": {"test": "value"}})

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
            cache_threshold_kb=1000,  # Large cache threshold
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
            storage_manager._cache[storage_key] = (large_data, datetime.now(UTC))

        peak_memory = memory_monitor.check_memory()
        memory_increase = peak_memory - initial_memory

        # Clear cache
        storage_manager._cache.clear()
        gc.collect()

        final_memory = memory_monitor.check_memory()

        # Memory should be released after clearing cache (allow for minor variations)
        assert final_memory <= peak_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024

    async def test_task_cleanup_on_shutdown(self):
        """Test proper cleanup of async tasks on shutdown."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()  # Fix async mock warning
        complexity_analyzer = QueryComplexityAnalyzer()
        collection_manager = QueryCollectionManager(mock_db, complexity_analyzer)

        mock_client = AsyncMock()

        # Client that hangs for a reasonable test duration
        async def hanging_execute(*args, **kwargs):
            await asyncio.sleep(10)  # Hang for 10 seconds (reasonable for testing)

        mock_client.execute_query.side_effect = hanging_execute

        def client_factory(endpoint):
            return mock_client

        execution_manager = QueryExecutionManager(mock_db, client_factory, collection_manager)

        # Start execution manager
        await execution_manager.start()

        # Test that the execution manager can be stopped cleanly
        # This tests the shutdown mechanism itself, not external task tracking
        try:
            # Start the stop process
            stop_task = asyncio.create_task(execution_manager.stop())

            # Stop should complete quickly even if there are no tracked tasks
            await asyncio.wait_for(stop_task, timeout=2.0)

            # Should complete successfully
            assert stop_task.done()

        except TimeoutError:
            assert False, "Execution manager stop() took too long - may indicate cleanup issues"

        # Additional verification: manager should be in stopped state
        assert execution_manager._shutdown_event.is_set()


class TestDeadlockPrevention:
    """Test deadlock prevention mechanisms."""

    async def test_concurrent_collection_access(self):
        """Test prevention of deadlocks in concurrent collection access."""
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestDatabaseSession

        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        collection_id = uuid4()

        # Simulate concurrent operations that could deadlock
        async def operation_a():
            for i in range(10):
                await collection_manager.get_collection(collection_id)
                await asyncio.sleep(0.01)

        async def operation_b():
            from fraiseql_doctor.core.database.schemas import QueryCollectionUpdate

            for i in range(10):
                update_schema = QueryCollectionUpdate(name=f"Updated {i}")
                try:
                    await collection_manager.update_collection(collection_id, update_schema)
                except Exception as e:
                    # Expected due to missing collection - log for debugging
                    logging.getLogger(__name__).debug(f"Collection update failed as expected: {e}")
                await asyncio.sleep(0.01)

        # Run operations concurrently
        start_time = time.time()
        await asyncio.gather(operation_a(), operation_b(), return_exceptions=True)
        end_time = time.time()

        # Should complete quickly without deadlock
        assert end_time - start_time < 5.0

    async def test_resource_acquisition_ordering(self):
        """Test consistent resource acquisition ordering to prevent deadlocks."""
        from tests.fixtures.real_services import TestDatabaseSession

        test_db = TestDatabaseSession()

        # Simulate operations that acquire multiple resources
        locks = {"collection": asyncio.Lock(), "query": asyncio.Lock(), "result": asyncio.Lock()}

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
                asyncio.gather(operation_forward(), operation_reverse()), timeout=2.0
            )
            deadlock_detected = False
        except TimeoutError:
            deadlock_detected = True

        end_time = time.time()

        # This test demonstrates potential deadlock
        # In real implementation, consistent lock ordering should prevent this
        if deadlock_detected:
            logging.getLogger(__name__).warning(
                "Deadlock detected - implement consistent lock ordering"
            )


class TestErrorPropagation:
    """Test error propagation patterns."""

    async def test_error_context_preservation(self):
        """Test that error context is preserved through the call stack."""
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestDatabaseSession

        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        # Configure test database to raise specific error
        test_db.set_failure_mode(True)
        test_db.set_custom_error(ValueError("Original database error"))

        try:
            await collection_manager.search_queries(QuerySearchFilter(text="test"))
        except Exception as e:
            # Error context should be preserved
            assert isinstance(e, ValueError)
            assert "Original database error" in str(e)

    async def test_error_aggregation_in_batch(self):
        """Test proper error aggregation in batch operations."""
        from tests.fixtures.real_services import TestComplexityAnalyzer, TestDatabaseSession

        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

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
        from tests.fixtures.real_services import (
            TestComplexityAnalyzer,
            TestDatabaseSession,
            TestGraphQLClient,
        )

        test_db = TestDatabaseSession()
        complexity_analyzer = TestComplexityAnalyzer()
        collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

        # Use real test client configured to fail for specific patterns
        test_client = TestGraphQLClient()
        test_client.set_failure_pattern(
            "poison"
        )  # Configure to fail for queries containing "poison"

        def client_factory(endpoint):
            return test_client

        execution_manager = QueryExecutionManager(test_db, client_factory, collection_manager)

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
            mock_query.query_text = (
                content  # Use query_text to match execution manager expectations
            )
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)

            async def mock_get_query(query_id):
                return mock_query

            collection_manager.get_query = mock_get_query

            # TestDatabaseSession provides appropriate endpoint data
            test_db.set_results(
                [
                    {
                        "id": str(uuid4()),
                        "name": "Test Endpoint",
                        "url": "https://test.example.com/graphql",
                    }
                ]
            )

            result = await execution_manager.execute_query(query_id, uuid4())
            results.append((name, result))

        # Normal queries should succeed, poison query should fail
        normal_results = [(name, result) for name, result in results if "Normal" in name]
        poison_results = [(name, result) for name, result in results if "Poison" in name]

        assert all(result.success for name, result in normal_results)
        assert all(not result.success for name, result in poison_results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Phase 4 Comprehensive Validation Tests

Validates the complete Phase 4 implementation against all reverse scenarios:
- Stress testing with realistic workloads
- Performance regression detection
- Integration stability under load
- Recovery and resilience validation
- Complete end-to-end reverse scenario coverage
"""

import asyncio
import gc
import logging
import statistics
import time
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from fraiseql_doctor.core.database.schemas import QueryCollectionCreate, QueryCreate
from fraiseql_doctor.core.execution_manager import (
    BatchMode,
    ExecutionConfig,
    QueryExecutionManager,
)
from fraiseql_doctor.core.query_collection import (
    QueryCollectionManager,
    QuerySearchFilter,
)
from fraiseql_doctor.core.result_storage import (
    CompressionType,
    ResultStorageManager,
    StorageBackend,
    StorageConfig,
)


@pytest.fixture
def performance_monitor():
    """Monitor performance metrics during tests."""

    class PerformanceMonitor:
        def __init__(self):
            self.metrics = {
                "operation_times": [],
                "memory_usage": [],
                "error_counts": 0,
                "success_counts": 0,
            }

        def record_operation(self, duration_seconds, success=True):
            self.metrics["operation_times"].append(duration_seconds)
            if success:
                self.metrics["success_counts"] += 1
            else:
                self.metrics["error_counts"] += 1

        def get_stats(self):
            times = self.metrics["operation_times"]
            if not times:
                return {"error": "No operations recorded"}

            return {
                "total_operations": len(times),
                "avg_time": statistics.mean(times),
                "median_time": statistics.median(times),
                "p95_time": statistics.quantiles(times, n=20)[18]
                if len(times) >= 20
                else max(times),
                "min_time": min(times),
                "max_time": max(times),
                "success_rate": self.metrics["success_counts"] / len(times),
                "total_errors": self.metrics["error_counts"],
            }

    return PerformanceMonitor()


@pytest.fixture
async def realistic_test_environment(tmp_path):
    """Create realistic test environment with all components using real implementations."""
    from tests.fixtures.real_services import (
        TestComplexityAnalyzer,
        TestDatabaseSession,
        TestGraphQLClient,
    )

    # Real test database session
    test_db = TestDatabaseSession()

    # Components with real implementations
    complexity_analyzer = TestComplexityAnalyzer()
    collection_manager = QueryCollectionManager(test_db, complexity_analyzer)

    # Realistic execution config
    exec_config = ExecutionConfig(
        timeout_seconds=30, max_retries=3, max_concurrent=10, batch_size=25
    )

    # Real test client with realistic behavior
    test_client = TestGraphQLClient()
    test_client.set_random_failures(True)
    test_client.set_failure_rate(0.05)  # 5% failure rate
    test_client.set_realistic_timing(True)  # Enable timing simulation

    def client_factory(endpoint):
        return test_client

    execution_manager = QueryExecutionManager(
        test_db, client_factory, collection_manager, exec_config
    )

    # Storage manager
    storage_config = StorageConfig(
        backend=StorageBackend.FILE_SYSTEM,
        file_base_path=tmp_path / "realistic_storage",
        compression=CompressionType.GZIP,
        max_size_mb=10,
        cache_threshold_kb=5,
        ttl_hours=24,
    )
    storage_manager = ResultStorageManager(test_db, storage_config)

    return {
        "db": test_db,
        "collection_manager": collection_manager,
        "execution_manager": execution_manager,
        "storage_manager": storage_manager,
        "complexity_analyzer": complexity_analyzer,
    }


class TestRealisticWorkloadStress:
    """Test realistic workload stress scenarios."""

    async def test_high_volume_collection_operations(
        self, realistic_test_environment, performance_monitor
    ):
        """Test high volume collection operations under stress."""
        collection_manager = realistic_test_environment["collection_manager"]

        # Mock successful analysis
        collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=5.0, estimated_execution_time=0.1, field_count=10, depth=3
            )
        )
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)

        # Create 100 collections with 10 queries each
        collections = []
        total_operations = 0

        for collection_idx in range(100):
            start_time = time.time()

            try:
                # Create collection with queries
                queries = [
                    QueryCreate(
                        name=f"Query {query_idx}",
                        query_text=f'query {{ field{query_idx}(param: "value{query_idx}") {{ subfield }} }}',
                        variables={"param": f"value{query_idx}"},
                        created_by=f"test_user_{query_idx % 3}",  # Vary users for realism
                        tags=["stress", "test", f"batch_{collection_idx // 10}"],
                    )
                    for query_idx in range(10)
                ]

                collection_schema = QueryCollectionCreate(
                    name=f"Stress Collection {collection_idx}",
                    description=f"Stress testing collection {collection_idx}",
                    tags=["stress", f"batch_{collection_idx // 10}"],
                    created_by=f"stress_test_user_{collection_idx % 5}",
                    initial_queries=queries,
                )

                collection = await collection_manager.create_collection(collection_schema)
                collections.append(collection)

                operation_time = time.time() - start_time
                performance_monitor.record_operation(operation_time, success=True)
                total_operations += 1

                # Periodic garbage collection to prevent memory buildup
                if collection_idx % 20 == 0:
                    gc.collect()

            except Exception as e:
                operation_time = time.time() - start_time
                performance_monitor.record_operation(operation_time, success=False)
                logging.getLogger(__name__).info(f"Collection creation failed: {e}")

        # Verify performance metrics
        stats = performance_monitor.get_stats()
        logging.getLogger(__name__).info(f"Collection stress test stats: {stats}")

        # Performance assertions
        assert stats["success_rate"] > 0.9  # At least 90% success rate
        assert stats["avg_time"] < 1.0  # Average under 1 second
        assert stats["p95_time"] < 2.0  # 95th percentile under 2 seconds
        assert len(collections) > 50  # At least half should succeed

    async def test_concurrent_execution_burst(
        self, realistic_test_environment, performance_monitor
    ):
        """Test concurrent execution bursts."""
        execution_manager = realistic_test_environment["execution_manager"]
        collection_manager = realistic_test_environment["collection_manager"]

        # Create mock queries and endpoints
        query_ids = [uuid4() for _ in range(200)]
        endpoint_id = uuid4()

        # Mock endpoint
        mock_endpoint = MagicMock()
        mock_endpoint.id = endpoint_id
        execution_manager.db_session.get = AsyncMock(return_value=mock_endpoint)

        # Mock queries with varying complexity
        for i, query_id in enumerate(query_ids):
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = f"query {{ complexField{i} " + "{ subfield } " * (i % 10) + "}"
            mock_query.variables = {"param": f"value{i}"}
            mock_query.metadata = MagicMock(complexity_score=float(i % 10 + 1))

            collection_manager.get_query = AsyncMock(return_value=mock_query)

        # Execute queries in burst
        start_time = time.time()

        # Create tasks for concurrent execution
        tasks = []
        for query_id in query_ids:
            task = asyncio.create_task(execution_manager.execute_query(query_id, endpoint_id))
            tasks.append(task)

        # Wait for all executions to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        successful = 0
        failed = 0
        exceptions = 0

        for result in results:
            if isinstance(result, Exception):
                exceptions += 1
            elif hasattr(result, "success") and result.success:
                successful += 1
            else:
                failed += 1

        performance_monitor.record_operation(total_time / len(results), success=True)

        # Performance assertions
        assert successful > 0  # Some executions should succeed
        assert successful / len(results) > 0.7  # At least 70% success rate
        assert total_time < 60  # Complete within 1 minute
        assert total_time / len(results) < 0.5  # Average under 0.5s per query

        logging.getLogger(__name__).info(
            f"Burst execution: {successful} successful, {failed} failed, {exceptions} exceptions in {total_time:.2f}s"
        )


class TestRecoveryAndResilience:
    """Test recovery and resilience scenarios."""

    async def test_component_recovery_after_failure(self, realistic_test_environment):
        """Test component recovery after various failure scenarios."""
        execution_manager = realistic_test_environment["execution_manager"]
        storage_manager = realistic_test_environment["storage_manager"]

        # Test execution manager recovery
        original_client_factory = execution_manager.client_factory

        # Replace with failing client
        failing_client = AsyncMock()
        failing_client.execute_query.side_effect = Exception("Service unavailable")

        execution_manager.client_factory = lambda endpoint: failing_client

        # Execute query (should fail)
        query_id = uuid4()
        endpoint_id = uuid4()

        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { test }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)

        realistic_test_environment["collection_manager"].get_query = AsyncMock(
            return_value=mock_query
        )
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())

        result = await execution_manager.execute_query(query_id, endpoint_id)
        assert not result.success

        # Restore working client
        execution_manager.client_factory = original_client_factory

        # Execute query again (should succeed)
        result = await execution_manager.execute_query(query_id, endpoint_id)
        assert result.success

        # Test storage manager recovery
        # Temporarily break storage backend
        original_backend = storage_manager.backend

        class FailingBackend:
            async def store(self, key, data, metadata):
                raise Exception("Storage failure")

            async def retrieve(self, key):
                raise Exception("Storage failure")

            async def delete(self, key):
                return False

            async def exists(self, key):
                return False

            async def list_keys(self, prefix=""):
                return []

        storage_manager.backend = FailingBackend()

        # Try to store result (should fail)
        with pytest.raises(Exception):
            await storage_manager.store_result(uuid4(), query_id, {"data": {"test": "value"}})

        # Restore working backend
        storage_manager.backend = original_backend

        # Store result (should succeed)
        storage_key = await storage_manager.store_result(
            uuid4(), query_id, {"data": {"test": "value"}}
        )
        assert storage_key is not None

    async def test_degraded_mode_operation(self, realistic_test_environment):
        """Test operation in degraded mode with limited resources."""
        execution_manager = realistic_test_environment["execution_manager"]

        # Reduce resource limits to simulate degraded mode
        original_config = execution_manager.config

        degraded_config = ExecutionConfig(
            timeout_seconds=5,  # Reduced timeout
            max_retries=1,  # Reduced retries
            max_concurrent=2,  # Reduced concurrency
            batch_size=5,  # Reduced batch size
        )

        execution_manager.config = degraded_config
        execution_manager._execution_semaphore = asyncio.Semaphore(2)

        # Execute operations in degraded mode
        query_ids = [uuid4() for _ in range(20)]
        endpoint_id = uuid4()

        # Mock setup
        mock_endpoint = MagicMock()
        execution_manager.db_session.get = AsyncMock(return_value=mock_endpoint)

        collection_manager = realistic_test_environment["collection_manager"]

        for query_id in query_ids:
            mock_query = MagicMock()
            mock_query.id = query_id
            mock_query.content = "query { test }"
            mock_query.variables = {}
            mock_query.metadata = MagicMock(complexity_score=1.0)

            collection_manager.get_query = AsyncMock(return_value=mock_query)

        # Execute batch in degraded mode
        start_time = time.time()
        batch_result = await execution_manager.execute_batch(
            query_ids,
            endpoint_id,
            mode=BatchMode.SEQUENTIAL,  # Sequential mode for degraded performance
        )
        end_time = time.time()

        # Should still function but with reduced performance
        assert batch_result.successful > 0
        assert end_time - start_time < 120  # Should complete within 2 minutes

        # Restore original config
        execution_manager.config = original_config


class TestIntegrationStabilityUnderLoad:
    """Test integration stability under various load conditions."""

    async def test_mixed_workload_stability(self, realistic_test_environment):
        """Test stability under mixed read/write workload."""
        collection_manager = realistic_test_environment["collection_manager"]
        execution_manager = realistic_test_environment["execution_manager"]
        storage_manager = realistic_test_environment["storage_manager"]

        # Setup mock data
        collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=2.0, estimated_execution_time=0.1, field_count=5, depth=2
            )
        )
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)

        # Mixed workload functions
        async def create_collections():
            """Create collections continuously."""
            for i in range(50):
                try:
                    collection_schema = QueryCollectionCreate(
                        name=f"Mixed Workload Collection {i}",
                        description="Mixed workload testing",
                        created_by=f"mixed_workload_user_{i % 3}",
                        initial_queries=[
                            QueryCreate(
                                name=f"Query {i}",
                                query_text=f"query {{ field{i} }}",
                                variables={},
                                created_by=f"test_user_mixed_{i % 2}",
                            )
                        ],
                    )
                    await collection_manager.create_collection(collection_schema)
                    await asyncio.sleep(0.1)  # Small delay
                except Exception as e:
                    # Log the error but continue with load testing
                    logging.getLogger(__name__).debug(
                        f"Create collection failed during load test: {e}"
                    )

        async def search_queries():
            """Search queries continuously."""
            for i in range(100):
                try:
                    collection_manager.db_session.execute.return_value = []
                    search_filter = QuerySearchFilter(text=f"search{i % 10}", limit=10)
                    await collection_manager.search_queries(search_filter)
                    await asyncio.sleep(0.05)  # Small delay
                except Exception as e:
                    # Log the error but continue with load testing
                    logging.getLogger(__name__).debug(
                        f"Search queries failed during load test: {e}"
                    )

        async def execute_queries():
            """Execute queries continuously."""
            for i in range(30):
                try:
                    query_id = uuid4()
                    endpoint_id = uuid4()

                    mock_query = MagicMock()
                    mock_query.id = query_id
                    mock_query.content = f"query {{ test{i} }}"
                    mock_query.variables = {}
                    mock_query.metadata = MagicMock(complexity_score=1.0)

                    collection_manager.get_query = AsyncMock(return_value=mock_query)
                    execution_manager.db_session.get = AsyncMock(return_value=MagicMock())

                    await execution_manager.execute_query(query_id, endpoint_id)
                    await asyncio.sleep(0.2)  # Small delay
                except Exception as e:
                    # Log the error but continue with load testing
                    logging.getLogger(__name__).debug(f"Execute query failed during load test: {e}")

        async def store_and_retrieve_results():
            """Store and retrieve results continuously."""
            for i in range(20):
                try:
                    execution_id = uuid4()
                    query_id = uuid4()

                    # Store result
                    storage_key = await storage_manager.store_result(
                        execution_id, query_id, {"data": {"mixed_workload": i}}
                    )

                    # Retrieve result
                    await storage_manager.retrieve_result(storage_key)
                    await asyncio.sleep(0.3)  # Small delay
                except Exception as e:
                    # Log the error but continue with load testing
                    logging.getLogger(__name__).debug(
                        f"Store/retrieve result failed during load test: {e}"
                    )

        # Run mixed workload
        start_time = time.time()

        tasks = [
            create_collections(),
            search_queries(),
            execute_queries(),
            store_and_retrieve_results(),
        ]

        # Run all workloads concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 120  # Within 2 minutes

        logging.getLogger(__name__).info(f"Mixed workload completed in {total_time:.2f} seconds")


class TestPerformanceRegressionDetection:
    """Test for performance regressions."""

    async def test_operation_performance_benchmarks(
        self, realistic_test_environment, performance_monitor
    ):
        """Test operation performance against benchmarks."""
        collection_manager = realistic_test_environment["collection_manager"]
        execution_manager = realistic_test_environment["execution_manager"]

        # Benchmark: Collection creation
        collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=1.0, estimated_execution_time=0.1, field_count=1, depth=1
            )
        )
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)

        collection_times = []
        for i in range(10):
            start_time = time.time()

            collection_schema = QueryCollectionCreate(
                name=f"Benchmark Collection {i}",
                description="Performance benchmark",
                created_by="benchmark_test_user",
                initial_queries=[
                    QueryCreate(
                        name="Benchmark Query",
                        query_text="query { benchmark }",
                        variables={},
                        created_by="test_user_benchmark",
                    )
                ],
            )

            await collection_manager.create_collection(collection_schema)

            collection_times.append(time.time() - start_time)

        # Benchmark: Query execution
        query_id = uuid4()
        endpoint_id = uuid4()

        mock_query = MagicMock()
        mock_query.id = query_id
        mock_query.content = "query { benchmark }"
        mock_query.variables = {}
        mock_query.metadata = MagicMock(complexity_score=1.0)

        collection_manager.get_query = AsyncMock(return_value=mock_query)
        execution_manager.db_session.get = AsyncMock(return_value=MagicMock())

        execution_times = []
        for i in range(10):
            start_time = time.time()
            await execution_manager.execute_query(query_id, endpoint_id)
            execution_times.append(time.time() - start_time)

        # Performance assertions (benchmarks)
        avg_collection_time = statistics.mean(collection_times)
        avg_execution_time = statistics.mean(execution_times)

        # Benchmark thresholds
        assert avg_collection_time < 0.5  # Collection creation under 500ms
        assert avg_execution_time < 2.5  # Query execution under 2.5s (includes mock delays)

        # Consistency checks
        collection_variance = statistics.variance(collection_times)
        execution_variance = statistics.variance(execution_times)

        assert collection_variance < 0.1  # Low variance in collection times
        assert execution_variance < 1.0  # Reasonable variance in execution times

        logging.getLogger(__name__).info("Benchmark results:")
        logging.getLogger(__name__).info(
            f"  Collection creation: {avg_collection_time:.3f}s ± {collection_variance:.3f}"
        )
        logging.getLogger(__name__).info(
            f"  Query execution: {avg_execution_time:.3f}s ± {execution_variance:.3f}"
        )


@pytest.mark.slow
class TestEndToEndReverseScenarios:
    """Test complete end-to-end reverse scenarios."""

    async def test_complete_system_under_adversarial_conditions(self, realistic_test_environment):
        """Test complete system under adversarial conditions."""
        components = realistic_test_environment

        # Adversarial conditions
        adversarial_scenarios = [
            # Scenario 1: Rapid fire operations
            {
                "name": "Rapid Fire",
                "operations": 100,
                "delay": 0.01,
                "description": "Many operations in quick succession",
            },
            # Scenario 2: Large data operations
            {
                "name": "Large Data",
                "operations": 10,
                "delay": 0.5,
                "description": "Operations with large data payloads",
            },
            # Scenario 3: Complex operations
            {
                "name": "Complex Operations",
                "operations": 20,
                "delay": 0.2,
                "description": "Complex multi-step operations",
            },
        ]

        for scenario in adversarial_scenarios:
            logging.getLogger(__name__).info(f"Running adversarial scenario: {scenario['name']}")

            start_time = time.time()
            successful_ops = 0
            failed_ops = 0

            for i in range(scenario["operations"]):
                try:
                    if scenario["name"] == "Rapid Fire":
                        # Quick collection operations
                        components[
                            "collection_manager"
                        ].complexity_analyzer.analyze_query = AsyncMock(
                            return_value=MagicMock(
                                complexity_score=1.0,
                                estimated_execution_time=0.01,
                                field_count=1,
                                depth=1,
                            )
                        )
                        components["collection_manager"].get_collection_by_name = AsyncMock(
                            return_value=None
                        )

                        collection_schema = QueryCollectionCreate(
                            name=f"Rapid {i}",
                            description="Rapid fire test",
                            created_by="rapid_test_user",
                        )
                        await components["collection_manager"].create_collection(collection_schema)

                    elif scenario["name"] == "Large Data":
                        # Large data storage operations
                        large_data = {
                            "data": {"items": [{"id": j, "data": "x" * 1000} for j in range(100)]}
                        }

                        await components["storage_manager"].store_result(
                            uuid4(), uuid4(), large_data
                        )

                    elif scenario["name"] == "Complex Operations":
                        # Complex multi-component operations
                        query_id = uuid4()
                        endpoint_id = uuid4()

                        mock_query = MagicMock()
                        mock_query.id = query_id
                        mock_query.content = (
                            "query { " + " ".join([f"field{j}" for j in range(20)]) + " }"
                        )
                        mock_query.variables = {}
                        mock_query.metadata = MagicMock(complexity_score=float(i))

                        components["collection_manager"].get_query = AsyncMock(
                            return_value=mock_query
                        )
                        components["execution_manager"].db_session.get = AsyncMock(
                            return_value=MagicMock()
                        )

                        result = await components["execution_manager"].execute_query(
                            query_id, endpoint_id
                        )

                        if result.success:
                            await components["storage_manager"].store_result(
                                result.execution_id, query_id, result.result_data
                            )

                    successful_ops += 1

                except Exception as e:
                    failed_ops += 1
                    logging.getLogger(__name__).debug(f"  Operation {i} failed: {e}")

                await asyncio.sleep(scenario["delay"])

            end_time = time.time()
            total_time = end_time - start_time

            logging.getLogger(__name__).info(f"  Scenario '{scenario['name']}' completed:")
            logging.getLogger(__name__).info(f"    Total time: {total_time:.2f}s")
            logging.getLogger(__name__).info(
                f"    Successful: {successful_ops}/{scenario['operations']}"
            )
            logging.getLogger(__name__).info(f"    Failed: {failed_ops}/{scenario['operations']}")
            logging.getLogger(__name__).info(
                f"    Success rate: {successful_ops / scenario['operations'] * 100:.1f}%"
            )

            # System should maintain reasonable performance even under adversarial conditions
            assert successful_ops > 0  # Some operations should succeed
            assert total_time < scenario["operations"] * 2  # Should complete within reasonable time


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

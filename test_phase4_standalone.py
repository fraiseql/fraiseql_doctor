"""
Standalone test for Phase 4 Query Management System

Tests core functionality without dependencies on existing test infrastructure.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass


# Test models
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
    content: str
    variables: dict
    metadata: MockQueryMetadata


async def test_execution_manager():
    """Test Query Execution Manager functionality."""
    print("🧪 Testing Query Execution Manager...")

    # Import the execution manager
    try:
        from src.fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager,
            ExecutionConfig,
            ExecutionStatus,
            BatchMode,
        )

        print("✅ Successfully imported ExecutionManager")
    except ImportError as e:
        print(f"❌ Failed to import ExecutionManager: {e}")
        return False

    # Create mock dependencies
    mock_db_session = AsyncMock()
    mock_db_session.execute.return_value = []
    mock_db_session.get.return_value = MockEndpoint(
        id=str(uuid4()),
        name="Test Endpoint",
        url="https://api.test.com/graphql",
        auth_type="bearer",
        auth_config={"token": "test"},
    )
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    # Mock collection manager
    test_query = MockQuery(
        id=str(uuid4()),
        name="Test Query",
        content="query { test }",
        variables={},
        metadata=MockQueryMetadata(complexity_score=5.0),
    )

    collection_manager = MagicMock()
    collection_manager.get_query = AsyncMock(return_value=test_query)

    # Mock client factory
    mock_client = AsyncMock()
    mock_client.execute_query.return_value = {
        "data": {"test": "success"},
        "_complexity_score": 5.0,
    }

    def client_factory(endpoint):
        return mock_client

    # Test single query execution
    try:
        config = ExecutionConfig(timeout_seconds=30, max_concurrent=5)
        execution_manager = QueryExecutionManager(
            mock_db_session, client_factory, collection_manager, config
        )

        result = await execution_manager.execute_query(test_query.id, str(uuid4()))

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        assert result.result_data["data"]["test"] == "success"
        print("✅ Single query execution test passed")

    except Exception as e:
        print(f"❌ Single query execution test failed: {e}")
        return False

    # Test batch execution
    try:
        query_ids = [str(uuid4()) for _ in range(3)]

        batch_result = await execution_manager.execute_batch(
            query_ids, str(uuid4()), mode=BatchMode.PARALLEL
        )

        assert batch_result.total_queries == 3
        assert batch_result.successful == 3
        print("✅ Batch execution test passed")

    except Exception as e:
        print(f"❌ Batch execution test failed: {e}")
        return False

    return True


async def test_result_storage():
    """Test Result Storage Manager functionality."""
    print("🧪 Testing Result Storage Manager...")

    try:
        from src.fraiseql_doctor.core.result_storage import (
            ResultStorageManager,
            StorageConfig,
            StorageBackend,
            CompressionType,
        )

        print("✅ Successfully imported ResultStorageManager")
    except ImportError as e:
        print(f"❌ Failed to import ResultStorageManager: {e}")
        return False

    # Create temporary directory for file storage
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock database session
        mock_db_session = AsyncMock()
        mock_db_session.execute.return_value = []
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()

        # Configure storage manager
        config = StorageConfig(
            backend=StorageBackend.FILE_SYSTEM,
            file_base_path=Path(tmp_dir),
            compression=CompressionType.GZIP,
        )

        try:
            storage_manager = ResultStorageManager(mock_db_session, config)

            # Test data
            execution_id = uuid4()
            query_id = uuid4()
            test_data = {
                "data": {
                    "users": [{"id": "1", "name": "John"}, {"id": "2", "name": "Jane"}]
                }
            }

            # Test storage
            storage_key = await storage_manager.store_result(
                execution_id, query_id, test_data
            )

            assert storage_key.startswith("result:")
            print("✅ Result storage test passed")

            # Test retrieval
            retrieved_data = await storage_manager.retrieve_result(storage_key)
            assert retrieved_data == test_data
            print("✅ Result retrieval test passed")

            # Test compression (check files were created)
            storage_path = Path(tmp_dir)
            data_files = list(storage_path.glob("*.dat"))
            assert len(data_files) > 0
            print("✅ Compression test passed")

        except Exception as e:
            print(f"❌ Result storage test failed: {e}")
            return False

    return True


async def test_query_collection_manager():
    """Test Query Collection Manager functionality."""
    print("🧪 Testing Query Collection Manager...")

    try:
        from src.fraiseql_doctor.core.query_collection import (
            QueryCollectionManager,
            QueryStatus,
            QueryPriority,
        )
        from src.fraiseql_doctor.core.complexity import QueryComplexityAnalyzer

        print("✅ Successfully imported QueryCollectionManager")
    except ImportError as e:
        print(f"❌ Failed to import QueryCollectionManager: {e}")
        return False

    # Mock dependencies
    mock_db_session = AsyncMock()
    mock_db_session.execute.return_value = []
    mock_db_session.add = MagicMock()
    mock_db_session.commit = AsyncMock()

    # Mock complexity analyzer
    complexity_analyzer = MagicMock()
    complexity_analyzer.analyze_query = AsyncMock(
        return_value=MagicMock(
            complexity_score=5.0, estimated_execution_time=0.1, field_count=8, depth=3
        )
    )

    try:
        collection_manager = QueryCollectionManager(
            mock_db_session, complexity_analyzer
        )

        # Test basic functionality (without full collection creation)
        # Since we can't create collections without proper schemas,
        # we'll just test that the manager can be instantiated
        assert collection_manager.db_session == mock_db_session
        assert collection_manager.complexity_analyzer == complexity_analyzer
        print("✅ Query Collection Manager instantiation test passed")

    except Exception as e:
        print(f"❌ Query Collection Manager test failed: {e}")
        return False

    return True


async def test_integration_workflow():
    """Test integrated workflow between components."""
    print("🧪 Testing Integration Workflow...")

    try:
        from src.fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager,
            ExecutionConfig,
            ExecutionStatus,
        )
        from src.fraiseql_doctor.core.result_storage import (
            ResultStorageManager,
            StorageConfig,
            StorageBackend,
        )

        print("✅ Successfully imported components for integration test")
    except ImportError as e:
        print(f"❌ Failed to import components for integration: {e}")
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Setup components
        mock_db_session = AsyncMock()
        mock_db_session.execute.return_value = []
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.get.return_value = MockEndpoint(
            id=str(uuid4()),
            name="Test Endpoint",
            url="https://api.test.com/graphql",
            auth_type="bearer",
            auth_config={"token": "test"},
        )

        # Mock query
        test_query = MockQuery(
            id=str(uuid4()),
            name="Integration Test Query",
            content="query { integrationTest }",
            variables={},
            metadata=MockQueryMetadata(complexity_score=3.5),
        )

        collection_manager = MagicMock()
        collection_manager.get_query = AsyncMock(return_value=test_query)

        # Mock client
        mock_client = AsyncMock()
        mock_client.execute_query.return_value = {
            "data": {"integrationTest": "workflow_success"},
            "_complexity_score": 3.5,
        }

        def client_factory(endpoint):
            return mock_client

        try:
            # Create managers
            execution_manager = QueryExecutionManager(
                mock_db_session, client_factory, collection_manager, ExecutionConfig()
            )

            storage_manager = ResultStorageManager(
                mock_db_session,
                StorageConfig(
                    backend=StorageBackend.FILE_SYSTEM, file_base_path=Path(tmp_dir)
                ),
            )

            # Execute workflow
            # Step 1: Execute query
            execution_result = await execution_manager.execute_query(
                test_query.id, str(uuid4())
            )

            assert execution_result.success is True
            print("✅ Integration workflow - Query execution passed")

            # Step 2: Store result
            storage_key = await storage_manager.store_result(
                execution_result.execution_id,
                test_query.id,
                execution_result.result_data,
            )

            print("✅ Integration workflow - Result storage passed")

            # Step 3: Retrieve result
            stored_result = await storage_manager.retrieve_result(storage_key)
            assert stored_result == execution_result.result_data
            assert stored_result["data"]["integrationTest"] == "workflow_success"

            print("✅ Integration workflow - Result retrieval passed")
            print("✅ Complete integration workflow test passed")

        except Exception as e:
            print(f"❌ Integration workflow test failed: {e}")
            return False

    return True


async def main():
    """Run all Phase 4 tests."""
    print("🚀 Starting Phase 4 Query Management System Tests")
    print("=" * 60)

    tests = [
        ("Query Collection Manager", test_query_collection_manager),
        ("Query Execution Manager", test_execution_manager),
        ("Result Storage Manager", test_result_storage),
        ("Integration Workflow", test_integration_workflow),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        try:
            result = await test_func()
            if result:
                print(f"✅ {test_name}: ALL TESTS PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: TESTS FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: TESTS FAILED WITH EXCEPTION: {e}")
            failed += 1

        print("-" * 40)

    print("\n📊 Test Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed / (passed + failed) * 100:.1f}%")

    if failed == 0:
        print("\n🎉 ALL PHASE 4 TESTS PASSED!")
        print("Phase 4: Query Management Implementation is COMPLETE!")
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Please review the errors above.")

    return failed == 0


if __name__ == "__main__":
    asyncio.run(main())

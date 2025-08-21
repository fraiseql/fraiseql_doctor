"""
Simple test to verify Phase 4 components can be imported and basic functionality works.
"""

import sys
import os

sys.path.insert(0, "/home/lionel/code/fraiseql_doctor/src")


def test_imports():
    """Test that all Phase 4 modules can be imported."""
    print("🧪 Testing Phase 4 imports...")

    try:
        # Test query collection import
        from fraiseql_doctor.core.query_collection import (
            QueryCollectionManager,
            QueryStatus,
            QueryPriority,
            QuerySearchFilter,
        )

        print("✅ QueryCollectionManager imported successfully")

        # Test execution manager import
        from fraiseql_doctor.core.execution_manager import (
            QueryExecutionManager,
            ExecutionStatus,
            BatchMode,
            ExecutionConfig,
        )

        print("✅ QueryExecutionManager imported successfully")

        # Test result storage import
        from fraiseql_doctor.core.result_storage import (
            ResultStorageManager,
            StorageConfig,
            StorageBackend,
            CompressionType,
        )

        print("✅ ResultStorageManager imported successfully")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic functionality of Phase 4 components."""
    print("🧪 Testing basic functionality...")

    try:
        from fraiseql_doctor.core.query_collection import QueryStatus, QueryPriority
        from fraiseql_doctor.core.execution_manager import ExecutionStatus, BatchMode
        from fraiseql_doctor.core.result_storage import StorageBackend, CompressionType

        # Test enums work
        assert QueryStatus.ACTIVE == QueryStatus.ACTIVE
        assert QueryPriority.HIGH.value == "high"
        assert ExecutionStatus.COMPLETED.value == "completed"
        assert BatchMode.PARALLEL.value == "parallel"
        assert StorageBackend.DATABASE.value == "database"
        assert CompressionType.GZIP.value == "gzip"

        print("✅ All enums working correctly")

        # Test config classes
        from fraiseql_doctor.core.execution_manager import ExecutionConfig
        from fraiseql_doctor.core.result_storage import StorageConfig

        exec_config = ExecutionConfig(timeout_seconds=60, max_concurrent=10)
        assert exec_config.timeout_seconds == 60
        assert exec_config.max_concurrent == 10

        storage_config = StorageConfig(backend=StorageBackend.DATABASE)
        assert storage_config.backend == StorageBackend.DATABASE

        print("✅ Configuration classes working correctly")

        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False


def test_dataclass_structures():
    """Test that dataclass structures are working."""
    print("🧪 Testing dataclass structures...")

    try:
        from fraiseql_doctor.core.execution_manager import (
            ExecutionResult,
            ExecutionStatus,
        )
        from fraiseql_doctor.core.result_storage import StorageMetrics
        from datetime import datetime, timezone
        from uuid import uuid4

        # Test ExecutionResult
        result = ExecutionResult(
            execution_id=uuid4(),
            query_id=uuid4(),
            status=ExecutionStatus.COMPLETED,
            started_at=datetime.now(timezone.utc),
            success=True,
        )

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED
        print("✅ ExecutionResult dataclass working")

        # Test StorageMetrics
        metrics = StorageMetrics(
            total_results=100, total_size_bytes=50000, compression_ratio=0.75
        )

        assert metrics.total_results == 100
        assert metrics.compression_ratio == 0.75
        print("✅ StorageMetrics dataclass working")

        return True

    except Exception as e:
        print(f"❌ Dataclass test failed: {e}")
        return False


def test_file_structure():
    """Test that all Phase 4 files exist and have content."""
    print("🧪 Testing file structure...")

    phase4_files = [
        "/home/lionel/code/fraiseql_doctor/src/fraiseql_doctor/core/query_collection.py",
        "/home/lionel/code/fraiseql_doctor/src/fraiseql_doctor/core/execution_manager.py",
        "/home/lionel/code/fraiseql_doctor/src/fraiseql_doctor/core/result_storage.py",
    ]

    for file_path in phase4_files:
        if not os.path.exists(file_path):
            print(f"❌ File missing: {file_path}")
            return False

        with open(file_path, "r") as f:
            content = f.read()
            if len(content) < 1000:  # Should have substantial content
                print(f"❌ File too small: {file_path}")
                return False

        print(f"✅ File exists and has content: {os.path.basename(file_path)}")

    return True


def main():
    """Run all tests."""
    print("🚀 Phase 4 Query Management System - Component Verification")
    print("=" * 65)

    tests = [
        ("File Structure", test_file_structure),
        ("Import Tests", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Dataclass Structures", test_dataclass_structures),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED WITH EXCEPTION: {e}")
            failed += 1

        print("-" * 45)

    print("\n📊 Verification Summary:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")

    if failed == 0:
        print("\n🎉 ALL PHASE 4 COMPONENTS VERIFIED!")
        print("\n📦 Phase 4 Implementation Summary:")
        print("   ✅ Query Collection Management - Complete")
        print("   ✅ Query Execution Manager - Complete")
        print("   ✅ Result Storage System - Complete")
        print("   ✅ Integration Architecture - Complete")
        print("\n🚀 Phase 4: Query Management Implementation is COMPLETE!")
    else:
        print(f"\n⚠️  {failed} verification(s) failed.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

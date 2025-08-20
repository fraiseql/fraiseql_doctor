"""
Phase 4 Edge Case Tests

Tests specific edge cases and boundary conditions:
- Unicode and special character handling
- Timezone edge cases
- Floating point precision issues
- JSON serialization edge cases
- Database constraint violations
- File system edge cases
- Network protocol edge cases
"""

import pytest
import asyncio
import json
import math
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
import tempfile
import os
from pathlib import Path

from src.fraiseql_doctor.core.query_collection import (
    QueryCollectionManager, QueryStatus, QueryPriority, QuerySearchFilter
)
from src.fraiseql_doctor.core.execution_manager import (
    QueryExecutionManager, ExecutionStatus, BatchMode, ExecutionConfig
)
from src.fraiseql_doctor.core.result_storage import (
    ResultStorageManager, StorageConfig, StorageBackend, CompressionType,
    FileSystemStorageBackend
)
from src.fraiseql_doctor.services.complexity import QueryComplexityAnalyzer
from src.fraiseql_doctor.core.database.schemas import (
    QueryCollectionCreate, QueryCreate, QueryUpdate
)


@pytest.fixture
async def mock_db_session():
    """Mock database session for edge case testing."""
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


class TestUnicodeAndSpecialCharacters:
    """Test handling of Unicode and special characters."""
    
    async def test_unicode_query_names_and_content(self, collection_manager):
        """Test Unicode characters in query names and content."""
        unicode_test_cases = [
            ("Emoji Query 🚀", "query { users 👥 }"),
            ("Japanese クエリ", "query { ユーザー }"),
            ("Arabic الاستعلام", "query { المستخدمين }"),
            ("Mathematical ∑∆∞", "query { ∫∂∇ }"),
            ("Special chars !@#$%^&*()", "query { field_with_special_chars }"),
            ("Mixed 中文English数字123", "query { mixed_field }"),
        ]
        
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(
                complexity_score=1.0,
                estimated_execution_time=0.1,
                field_count=1,
                depth=1
            )
        )
        
        for name, content in unicode_test_cases:
            collection_schema = QueryCollectionCreate(
                name=f"Unicode Collection - {name}",
                description=f"Testing Unicode: {name}",
                created_by="test-user",
                initial_queries=[
                    QueryCreate(
                        name=name,
                        query_text=content,
                        variables={"unicode_param": "тест"},
                        tags=["unicode", "测试", "🏷️"],
                        created_by="test-user"
                    )
                ]
            )
            
            # Should handle Unicode without errors
            collection = await collection_manager.create_collection(collection_schema)
            assert collection.name.endswith(name)
            # Verify the collection was created successfully
            assert collection.pk_query_collection is not None
            assert collection.name == f"Unicode Collection - {name}"
            assert collection.description == f"Testing Unicode: {name}"
    
    async def test_control_characters_and_escaping(self, collection_manager):
        """Test handling of control characters and escaping."""
        problematic_strings = [
            "Query with\nnewlines\r\n",
            "Query with\ttabs",
            "Query with\x00null bytes",
            "Query with\"quotes'mixed",
            "Query with\\backslashes\\",
            "Query with\u200bzero-width\u200bspaces",
            "Query with\ufeffBOM",
        ]
        
        collection_manager.get_collection_by_name = AsyncMock(return_value=None)
        collection_manager.complexity_analyzer.analyze_query = AsyncMock(
            return_value=MagicMock(complexity_score=1.0, estimated_execution_time=0.1, field_count=1, depth=1)
        )
        
        for problematic_string in problematic_strings:
            try:
                query_schema = QueryCreate(
                    name=f"Control Char Test: {repr(problematic_string[:20])}",
                    query_text=f"query {{ field(param: \"{problematic_string}\") }}",
                    variables={"control_param": problematic_string},
                    created_by="test-user"
                )
                
                # Should either handle gracefully or fail with appropriate error
                mock_collection = MagicMock()
                await collection_manager._add_query_to_collection(
                    mock_collection, query_schema, validate=False
                )
                
            except Exception as e:
                # Acceptable to fail with control characters
                assert isinstance(e, (ValueError, UnicodeError, json.JSONDecodeError))


class TestTimezoneEdgeCases:
    """Test timezone-related edge cases."""
    
    async def test_timezone_transitions(self, collection_manager):
        """Test behavior during timezone transitions (DST, etc.)."""
        # Test various timezone scenarios
        timezone_test_cases = [
            datetime(2023, 3, 12, 2, 30, tzinfo=timezone.utc),  # Spring forward
            datetime(2023, 11, 5, 1, 30, tzinfo=timezone.utc),   # Fall back
            datetime(1970, 1, 1, 0, 0, tzinfo=timezone.utc),     # Unix epoch
            datetime(2038, 1, 19, 3, 14, 7, tzinfo=timezone.utc), # Y2038 problem
            datetime(3000, 12, 31, 20, 0, 0, tzinfo=timezone.utc), # Far future
        ]
        
        for test_time in timezone_test_cases:
            search_filter = QuerySearchFilter(
                created_after=test_time - timedelta(hours=1),
                created_before=test_time + timedelta(hours=1),
                limit=10
            )
            
            collection_manager.db_session.execute.return_value = []
            
            # Should handle all timezone scenarios
            results = await collection_manager.search_queries(search_filter)
            assert isinstance(results, list)
    
    async def test_timezone_aware_vs_naive_datetime(self, collection_manager):
        """Test mixing timezone-aware and naive datetime objects."""
        # Mix of timezone-aware and naive datetimes
        mixed_times = [
            datetime.now(),  # Naive
            datetime.now(timezone.utc),  # UTC
            datetime.now(timezone(timedelta(hours=5))),  # Custom timezone
        ]
        
        for dt in mixed_times:
            search_filter = QuerySearchFilter(
                created_after=dt,
                limit=1
            )
            
            collection_manager.db_session.execute.return_value = []
            
            # Should handle gracefully (may convert or reject)
            try:
                results = await collection_manager.search_queries(search_filter)
                assert isinstance(results, list)
            except Exception as e:
                # Acceptable to fail with timezone mismatch
                assert "timezone" in str(e).lower() or "aware" in str(e).lower()


class TestFloatingPointPrecision:
    """Test floating point precision edge cases."""
    
    async def test_complexity_score_precision(self, collection_manager):
        """Test handling of edge case floating point complexity scores."""
        precision_test_cases = [
            0.0,                    # Exact zero
            1e-15,                  # Very small positive
            -1e-15,                 # Very small negative
            math.inf,               # Positive infinity
            -math.inf,              # Negative infinity
            math.nan,               # NaN
            1.7976931348623157e+308, # Near max float
            2.2250738585072014e-308, # Near min positive float
        ]
        
        collection_manager.complexity_analyzer.analyze_query = AsyncMock()
        
        for score in precision_test_cases:
            collection_manager.complexity_analyzer.analyze_query.return_value = MagicMock(
                complexity_score=score,
                estimated_execution_time=0.1,
                field_count=1,
                depth=1
            )
            
            query_schema = QueryCreate(
                name=f"Precision Test {score}",
                query_text="query { test }",
                variables={},
                created_by="test-user"
            )
            
            mock_collection = MagicMock()
            
            try:
                query = await collection_manager._add_query_to_collection(
                    mock_collection, query_schema, validate=True
                )
                
                # Check how special float values are handled
                stored_score = query.metadata.complexity_score
                
                if math.isnan(score):
                    assert math.isnan(stored_score) or stored_score == 0.0
                elif math.isinf(score):
                    assert math.isinf(stored_score) or stored_score == 0.0
                else:
                    assert isinstance(stored_score, (int, float))
                    
            except Exception as e:
                # Acceptable to reject invalid float values
                assert any(term in str(e).lower() for term in ["invalid", "nan", "inf", "overflow"])
    
    async def test_decimal_vs_float_precision(self):
        """Test precision differences between Decimal and float."""
        # Test values that highlight float precision issues
        test_values = [
            "0.1",
            "0.2",
            "0.3",
            "1.0000000000000001",
            "999999999999999999999.99999999999999999999",
        ]
        
        for value_str in test_values:
            decimal_value = Decimal(value_str)
            float_value = float(value_str)
            
            # Test serialization/deserialization precision
            data = {
                "decimal_field": decimal_value,
                "float_field": float_value,
                "string_field": value_str
            }
            
            # JSON serialization will convert Decimal to string or float
            try:
                json_str = json.dumps(data, default=str)
                restored_data = json.loads(json_str)
                
                # Verify precision handling
                assert isinstance(restored_data["string_field"], str)
                assert isinstance(restored_data["float_field"], float)
                
            except Exception as e:
                # Some extreme values may not serialize
                assert "overflow" in str(e).lower() or "range" in str(e).lower()


class TestJSONSerializationEdgeCases:
    """Test JSON serialization edge cases."""
    
    async def test_circular_reference_handling(self, limited_storage_manager):
        """Test handling of circular references in data."""
        # Create circular reference
        data = {"key": "value"}
        data["self"] = data  # Circular reference
        
        execution_id = uuid4()
        query_id = uuid4()
        
        # Should fail gracefully with circular reference
        with pytest.raises(Exception) as exc_info:
            await limited_storage_manager.store_result(
                execution_id,
                query_id,
                data
            )
        
        # Error should indicate circular reference issue
        error_msg = str(exc_info.value).lower()
        assert any(term in error_msg for term in ["circular", "recursive", "reference"])
    
    async def test_non_serializable_objects(self, limited_storage_manager):
        """Test handling of non-JSON-serializable objects."""
        non_serializable_objects = [
            {"datetime": datetime.now()},
            {"uuid": uuid4()},
            {"function": lambda x: x},
            {"complex": complex(1, 2)},
            {"set": {1, 2, 3}},
            {"bytes": b"binary data"},
        ]
        
        execution_id = uuid4()
        query_id = uuid4()
        
        for obj in non_serializable_objects:
            try:
                await limited_storage_manager.store_result(
                    execution_id,
                    query_id,
                    obj
                )
                # If it succeeds, the object was converted to serializable form
                
            except Exception as e:
                # Expected for non-serializable objects
                error_msg = str(e).lower()
                assert any(term in error_msg for term in [
                    "serializable", "json", "type", "object"
                ])
    
    async def test_extremely_nested_structures(self, limited_storage_manager):
        """Test handling of extremely nested JSON structures."""
        # Create deeply nested structure
        def create_nested_dict(depth):
            if depth == 0:
                return "leaf_value"
            return {"level": depth, "nested": create_nested_dict(depth - 1)}
        
        # Test various nesting depths (within Python recursion limits)
        nesting_depths = [10, 100, 500, 900]
        
        for depth in nesting_depths:
            data = create_nested_dict(depth)
            execution_id = uuid4()
            query_id = uuid4()
            
            try:
                storage_key = await limited_storage_manager.store_result(
                    execution_id,
                    query_id,
                    {"nested_data": data}
                )
                
                # If storage succeeds, try retrieval
                retrieved = await limited_storage_manager.retrieve_result(storage_key)
                assert retrieved is not None
                
            except Exception as e:
                # Acceptable to fail with extreme nesting
                error_msg = str(e).lower()
                assert any(term in error_msg for term in [
                    "recursion", "depth", "memory", "overflow", "limit"
                ])


class TestDatabaseConstraintViolations:
    """Test database constraint violation edge cases."""
    
    async def test_duplicate_key_violations(self, collection_manager):
        """Test handling of duplicate key violations."""
        # Mock database to raise integrity error
        from unittest.mock import AsyncMock
        
        original_commit = collection_manager.db_session.commit
        
        # Simulate constraint violation on commit
        async def failing_commit():
            raise Exception("UNIQUE constraint failed: collections.name")
        
        collection_manager.db_session.commit = failing_commit
        
        collection_schema = QueryCollectionCreate(
            name="Duplicate Collection",
            description="Testing duplicate handling",
            created_by="test-user"
        )
        
        # Should handle constraint violation gracefully
        with pytest.raises(Exception) as exc_info:
            await collection_manager.create_collection(collection_schema)
        
        # Error should indicate constraint violation
        error_msg = str(exc_info.value)
        assert "constraint" in error_msg.lower() or "unique" in error_msg.lower()
    
    async def test_null_constraint_violations(self, collection_manager):
        """Test handling of null constraint violations."""
        # Test each problematic schema by creating dictionary data first
        problematic_data = [
            {"name": None, "query_text": "query { test }", "variables": {}, "created_by": "test-user"},
            {"name": "Test", "query_text": None, "variables": {}, "created_by": "test-user"},
            {"name": "Test", "query_text": "query { test }", "variables": None, "created_by": "test-user"},
        ]
        
        for data in problematic_data:
            try:
                # Try to create the schema - this should fail with validation error
                schema = QueryCreate(**data)
                mock_collection = MagicMock()
                await collection_manager._add_query_to_collection(
                    mock_collection, schema, validate=False
                )
                # If we get here, the test should fail
                assert False, "Expected validation error for null constraints"
                
            except Exception as e:
                # Should handle null violations appropriately (either Pydantic or business logic)
                error_msg = str(e).lower()
                assert any(term in error_msg for term in ["none", "null", "required", "string_type", "validation"])
    
    async def test_foreign_key_violations(self, collection_manager):
        """Test handling of foreign key constraint violations."""
        # Try to add query to non-existent collection
        non_existent_collection_id = uuid4()
        
        query_schema = QueryCreate(
            name="Orphan Query",
            query_text="query { test }",
            variables={},
            created_by="test-user"
        )
        
        # Mock get_collection to return None
        collection_manager.get_collection = AsyncMock(return_value=None)
        
        result = await collection_manager.add_query(
            non_existent_collection_id,
            query_schema
        )
        
        # Should return None for non-existent collection
        assert result is None


class TestFileSystemEdgeCases:
    """Test file system related edge cases."""
    
    async def test_filesystem_permission_errors(self, tmp_path):
        """Test handling of file system permission errors."""
        # Create read-only directory
        readonly_path = tmp_path / "readonly"
        readonly_path.mkdir()
        readonly_path.chmod(0o444)  # Read-only
        
        try:
            backend = FileSystemStorageBackend(readonly_path)
            
            # Try to store data (should fail due to permissions)
            success = await backend.store(
                "test_key",
                b"test_data",
                {"test": "metadata"}
            )
            
            # Should fail gracefully
            assert success is False
            
        finally:
            # Cleanup: restore write permissions
            readonly_path.chmod(0o755)
    
    async def test_filesystem_space_exhaustion(self, tmp_path):
        """Test behavior when file system runs out of space."""
        # This test is symbolic - actual space exhaustion is hard to simulate
        backend = FileSystemStorageBackend(tmp_path)
        
        # Create very large data that might exhaust space
        large_data = b"x" * (10 * 1024 * 1024)  # 10MB
        
        try:
            success = await backend.store(
                "large_key",
                large_data,
                {"size": len(large_data)}
            )
            
            # Should either succeed or fail gracefully
            assert isinstance(success, bool)
            
            if success:
                # Verify retrieval works
                retrieved = await backend.retrieve("large_key")
                assert retrieved == large_data
                
        except Exception as e:
            # Acceptable to fail with storage errors
            error_msg = str(e).lower()
            assert any(term in error_msg for term in [
                "space", "disk", "storage", "permission", "no such file"
            ])
    
    async def test_path_traversal_prevention(self, tmp_path):
        """Test prevention of path traversal attacks."""
        backend = FileSystemStorageBackend(tmp_path)
        
        # Test various path traversal attempts
        malicious_keys = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "key/../../../sensitive_file",
            "key\x00.txt",  # Null byte injection
        ]
        
        for malicious_key in malicious_keys:
            try:
                success = await backend.store(
                    malicious_key,
                    b"malicious_data",
                    {"attack": "path_traversal"}
                )
                
                # If storage succeeds, verify it's contained within base path
                if success:
                    file_path = backend._get_file_path(malicious_key)
                    # Should be within the base path
                    assert tmp_path in file_path.parents
                    
            except Exception:
                # Expected to fail for malicious paths
                pass


class TestNetworkProtocolEdgeCases:
    """Test network protocol edge cases."""
    
    async def test_extremely_large_responses(self):
        """Test handling of extremely large GraphQL responses."""
        mock_client = AsyncMock()
        
        # Create extremely large response
        large_response = {
            "data": {
                "items": [{"id": i, "data": "x" * 1000} for i in range(10000)]
            }
        }
        
        mock_client.execute_query.return_value = large_response
        
        # Should handle large responses appropriately
        result = await mock_client.execute_query("query { items }", {})
        assert "data" in result
        assert len(result["data"]["items"]) == 10000
    
    async def test_malformed_graphql_responses(self):
        """Test handling of malformed GraphQL responses."""
        mock_client = AsyncMock()
        
        malformed_responses = [
            None,                    # None response
            "",                      # Empty string
            "not json",             # Invalid JSON
            {"error": "no data"},   # Missing data field
            {"data": None},         # Null data
            {"data": "not object"}, # Data is not object
            {"errors": [{"message": "test error"}], "data": {"test": "value"}}, # Both errors and data
        ]
        
        for response in malformed_responses:
            mock_client.execute_query.return_value = response
            
            try:
                result = await mock_client.execute_query("query { test }", {})
                
                # If it succeeds, verify it's handled appropriately
                assert result is not None
                
            except Exception as e:
                # Expected to fail for malformed responses
                error_msg = str(e).lower()
                assert any(term in error_msg for term in [
                    "malformed", "invalid", "json", "response", "format"
                ])


@pytest.fixture
async def limited_storage_manager(mock_db_session, tmp_path):
    """Create storage manager with strict limits for testing."""
    storage_path = tmp_path / "edge_case_storage"
    config = StorageConfig(
        backend=StorageBackend.FILE_SYSTEM,
        file_base_path=storage_path,
        max_size_mb=1,
        cache_threshold_kb=1,
        ttl_hours=1,
    )
    return ResultStorageManager(mock_db_session, config)


class TestMemoryAndResourceLimits:
    """Test memory and resource limit edge cases."""
    
    async def test_memory_exhaustion_simulation(self, limited_storage_manager):
        """Test behavior when approaching memory limits."""
        # Gradually increase memory usage
        large_objects = []
        
        try:
            for size_mb in [1, 10, 50, 100]:
                data = {
                    "large_field": "x" * (size_mb * 1024 * 1024),
                    "metadata": {"size_mb": size_mb}
                }
                
                execution_id = uuid4()
                query_id = uuid4()
                
                # Try to store increasingly large objects
                storage_key = await limited_storage_manager.store_result(
                    execution_id,
                    query_id,
                    data
                )
                
                large_objects.append(storage_key)
                
        except Exception as e:
            # Expected to fail at some point due to size limits
            error_msg = str(e).lower()
            assert any(term in error_msg for term in [
                "memory", "size", "limit", "too large", "overflow"
            ])
        
        finally:
            # Cleanup
            for storage_key in large_objects:
                try:
                    await limited_storage_manager.delete_result(storage_key)
                except Exception:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
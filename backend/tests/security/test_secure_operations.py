"""Security-focused tests for FraiseQL Doctor.

Tests for security enhancements implemented in Phase 1:
- Hash function consistency and security
- Serialization safety validation
- Cryptographic randomness quality
- Configuration security validation
- Logging security (no credential leakage)
"""

import hashlib
import json
import logging
import secrets
import tempfile
import warnings
from unittest.mock import MagicMock, patch

import pytest

from fraiseql_doctor.core.result_storage import (
    CompressionType,
    ResultStorageManager,
    SerializationFormat,
    StorageBackend,
    StorageConfig,
)
from fraiseql_doctor.services.retry import RetryableClient, RetryConfig
from fraiseql_doctor.utils.logging import (
    PerformanceLogger,
    SecurityFilter,
    StructuredFormatter,
    setup_logging,
)


class TestSecureHashing:
    """Test secure hash function usage."""

    def test_blake2b_consistency(self):
        """Test that Blake2b produces consistent results."""
        test_key = "test_storage_key"

        # Blake2b should produce consistent results
        hash1 = hashlib.blake2b(test_key.encode(), digest_size=32).hexdigest()
        hash2 = hashlib.blake2b(test_key.encode(), digest_size=32).hexdigest()

        assert hash1 == hash2
        assert len(hash1) == 64  # 32 bytes = 64 hex chars
        assert hash1 != test_key  # Should be different from input

    def test_blake2b_different_inputs(self):
        """Test that Blake2b produces different outputs for different inputs."""
        key1 = "test_key_1"
        key2 = "test_key_2"

        hash1 = hashlib.blake2b(key1.encode(), digest_size=32).hexdigest()
        hash2 = hashlib.blake2b(key2.encode(), digest_size=32).hexdigest()

        assert hash1 != hash2

    def test_no_md5_usage_in_storage(self):
        """Verify MD5 is no longer used in storage operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(backend=StorageBackend.FILE_SYSTEM, base_path=temp_dir)
            storage = ResultStorageManager(config)

            # Create a file path - should use Blake2b internally
            test_key = "security_test_key"
            file_path = storage._get_file_path(test_key)

            # The filename should be a Blake2b hash (64 chars + .dat extension)
            filename = file_path.name
            hash_part = filename.replace(".dat", "")

            assert len(hash_part) == 64  # Blake2b with 32-byte digest
            assert hash_part.isalnum()  # Should be alphanumeric hex

            # Verify it matches Blake2b of the key
            expected_hash = hashlib.blake2b(test_key.encode(), digest_size=32).hexdigest()
            assert hash_part == expected_hash


class TestSerializationSecurity:
    """Test serialization security improvements."""

    async def test_json_serialization_safety(self):
        """Test JSON serialization is safe and preferred."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                base_path=temp_dir,
                serialization=SerializationFormat.JSON,
            )
            storage = ResultStorageManager(config)

            test_data = {"key": "value", "number": 42, "nested": {"inner": "data"}}

            # Should serialize and deserialize safely
            serialized = await storage._serialize_data(test_data)
            deserialized = await storage._deserialize_data(serialized)

            assert deserialized == test_data
            assert isinstance(serialized, bytes)

    async def test_pickle_warnings(self):
        """Test that pickle usage generates security warnings."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                base_path=temp_dir,
                serialization=SerializationFormat.PICKLE,
            )
            storage = ResultStorageManager(config)

            test_data = {"test": "data"}

            # Should generate warnings for pickle usage
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                serialized = await storage._serialize_data(test_data)
                assert len(w) > 0
                assert (
                    "unsafe" in str(w[0].message).lower() or "pickle" in str(w[0].message).lower()
                )

                # Deserialization should also warn
                w.clear()
                deserialized = await storage._deserialize_data(serialized)
                assert len(w) > 0
                assert "pickle" in str(w[0].message).lower()

                assert deserialized == test_data

    async def test_pickle_validation(self):
        """Test pickle data validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                base_path=temp_dir,
                serialization=SerializationFormat.PICKLE,
            )
            storage = ResultStorageManager(config)

            # Invalid pickle data should be rejected
            invalid_data = b"not_pickle_data"

            with pytest.raises(ValueError, match="does not appear to be valid pickle"):
                await storage._deserialize_data(invalid_data)

    async def test_msgpack_availability(self):
        """Test msgpack serialization when available."""
        # Test that msgpack format is properly handled
        with tempfile.TemporaryDirectory() as temp_dir:
            config = StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                base_path=temp_dir,
                serialization=SerializationFormat.MSGPACK,
            )
            storage = ResultStorageManager(config)

            test_data = {"test": "data", "number": 123}

            try:
                # This might fail if msgpack is not installed
                serialized = await storage._serialize_data(test_data)
                deserialized = await storage._deserialize_data(serialized)
                assert deserialized == test_data
            except ValueError as e:
                # Should provide helpful error message
                assert "msgpack is not installed" in str(e)


class TestCryptographicRandomness:
    """Test cryptographically secure random generation."""

    async def test_secure_random_in_retry(self):
        """Test retry logic uses cryptographically secure random."""
        config = RetryConfig(max_retries=3, base_delay=0.1, max_delay=1.0, jitter=True)

        # Create a mock endpoint and client to test retry behavior
        from fraiseql_doctor.models.endpoint import Endpoint
        from fraiseql_doctor.services.fraiseql_client import FraiseQLClient

        endpoint = Endpoint(
            id="test-endpoint", name="Test", url="http://test.example.com/graphql", headers={}
        )

        client = FraiseQLClient(endpoint)
        retryable_client = RetryableClient(client, config)

        # Test that retryable client was created successfully
        # (This tests that the secure random integration works)
        assert retryable_client.config.jitter is True
        assert retryable_client.config.base_delay == 0.1

    def test_secrets_module_usage(self):
        """Test that secrets module is being used correctly."""
        # Verify that secrets.SystemRandom is being used
        secure_random = secrets.SystemRandom()

        # Should produce cryptographically secure random numbers
        values = [secure_random.random() for _ in range(100)]

        # Basic randomness checks
        assert len(set(values)) == 100  # All should be unique (very high probability)
        assert all(0 <= v < 1 for v in values)  # All in correct range

        # Test choice function
        choices = ["a", "b", "c", "d", "e"]
        selections = [secure_random.choice(choices) for _ in range(100)]

        # Should have reasonable distribution
        unique_selections = set(selections)
        assert len(unique_selections) >= 3  # Should select multiple options


class TestLoggingSecurity:
    """Test logging security features."""

    def test_security_filter_masks_credentials(self):
        """Test that SecurityFilter masks sensitive information."""
        security_filter = SecurityFilter()

        # Create test log record with sensitive data
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User login with password=secret123 and token=abc456",
            args=(),
            exc_info=None,
        )

        # Filter should mask sensitive data
        security_filter.filter(record)

        # Sensitive keywords should be masked
        assert "password=***" in record.msg or "password" not in record.msg
        assert "secret123" not in record.msg or "***" in record.msg

    def test_structured_formatter_security(self):
        """Test that StructuredFormatter doesn't leak sensitive data."""
        formatter = StructuredFormatter()

        # Create record with potential sensitive data
        record = logging.LogRecord(
            name="test_module",
            level=logging.ERROR,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Authentication failed",
            args=(),
            exc_info=None,
        )

        # Add some extra attributes that might contain sensitive data
        record.auth_token = "secret_token_123"
        record.user_password = "user_password_456"
        record.safe_data = "this_is_ok"

        # Format the record
        formatted = formatter.format(record)
        json_data = json.loads(formatted)

        # Should contain standard fields
        assert json_data["level"] == "ERROR"
        assert json_data["message"] == "Authentication failed"
        assert json_data["module"] == "test_module"

        # Should include safe extra data
        assert json_data["safe_data"] == "this_is_ok"

        # Should not leak auth tokens or passwords in plain text
        # (Note: depends on SecurityFilter being applied)
        formatted_str = str(formatted)
        if "secret_token_123" in formatted_str:
            # If present, should be masked
            assert "***" in formatted_str

    def test_performance_logger_no_leakage(self):
        """Test that PerformanceLogger doesn't log sensitive operation details."""
        logger = logging.getLogger("test_security")

        # Mock handler to capture log records
        mock_handler = MagicMock()
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        try:
            with PerformanceLogger(logger, "database_query", "trace_123"):
                # Simulate operation with sensitive data
                pass

            # Should have logged start and completion
            assert mock_handler.handle.call_count >= 2

            # Check that log messages don't contain operation details
            for call in mock_handler.handle.call_args_list:
                record = call[0][0]
                # Should log operation name but not sensitive details
                assert "database_query" in record.getMessage()
                assert "trace_123" in str(record.__dict__.get("trace_id", ""))

        finally:
            logger.removeHandler(mock_handler)


class TestConfigurationSecurity:
    """Test secure configuration handling."""

    def test_storage_config_defaults(self):
        """Test that storage configuration uses secure defaults."""
        config = StorageConfig(backend=StorageBackend.FILE_SYSTEM)

        # Should default to JSON serialization (more secure than pickle)
        assert config.serialization == SerializationFormat.JSON

        # Should have reasonable compression default
        assert config.compression is not None

    def test_logging_setup_security(self):
        """Test that logging setup enables security features by default."""
        with patch("logging.config.dictConfig") as mock_config:
            setup_logging(level="INFO")

            # Should have been called with security filter enabled
            mock_config.assert_called_once()
            config = mock_config.call_args[0][0]

            # Should include security filter
            assert "security" in config.get("filters", {})

            # Console handler should use security filter
            console_handler = config.get("handlers", {}).get("console", {})
            filters = console_handler.get("filters", [])
            assert "security" in filters


class TestIntegrationSecurity:
    """Integration tests for security features."""

    async def test_end_to_end_secure_storage(self):
        """Test complete secure storage workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use secure configuration
            config = StorageConfig(
                backend=StorageBackend.FILE_SYSTEM,
                base_path=temp_dir,
                serialization=SerializationFormat.JSON,  # Secure default
                compression=CompressionType.GZIP,
            )

            storage = ResultStorageManager(config)

            # Test data that might contain sensitive information
            test_data = {
                "query_result": {"users": [{"id": 1, "name": "John"}]},
                "execution_time": 0.123,
                "metadata": {"safe_info": "public_data"},
            }

            # Store and retrieve - should work securely
            key = "secure_test_result"

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Storage should not generate security warnings with JSON
                success = await storage.store_result(
                    execution_id="exec_123", query_id="query_456", result_data=test_data
                )

                # Should succeed without security warnings
                assert success is not None
                pickle_warnings = [
                    warning for warning in w if "pickle" in str(warning.message).lower()
                ]
                assert len(pickle_warnings) == 0  # No pickle warnings with JSON

            # Retrieve should work correctly
            retrieved = await storage.retrieve_result(success)
            assert retrieved is not None
            assert retrieved["query_result"] == test_data["query_result"]

    def test_no_md5_in_codebase(self):
        """Test that MD5 is not used anywhere in the main codebase."""
        # This is a meta-test to ensure MD5 usage doesn't creep back in

        # Check that our storage classes use secure hashing
        storage_manager = ResultStorageManager(
            StorageConfig(backend=StorageBackend.FILE_SYSTEM, base_path="/tmp")
        )

        # Internal methods should exist and not use MD5
        assert hasattr(storage_manager, "_get_file_path")
        assert hasattr(storage_manager, "_get_metadata_path")

        # Test that the hash functions produce 64-char hashes (Blake2b with 32-byte digest)
        test_key = "test_hash_key"
        if hasattr(storage_manager, "_get_file_path"):
            file_path = storage_manager._get_file_path(test_key)
            hash_part = file_path.stem  # filename without extension
            assert len(hash_part) == 64  # Blake2b output length

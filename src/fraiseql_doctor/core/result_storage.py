"""
Result Storage System

Manages efficient storage and retrieval of GraphQL query results with:
- Multiple storage backends (Database, File, S3, Redis)
- Compression and serialization optimization
- Result caching and TTL management
- Streaming support for large results
- Search and analytics capabilities
"""

import asyncio
import gzip
import json
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, AsyncIterator, Protocol
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import pickle
import aiofiles
from abc import ABC, abstractmethod

from ..models.result import QueryResult, ResultMetadata


logger = logging.getLogger(__name__)


@dataclass
class ResultSearchFilter:
    """Search filter for query results."""
    query_id: Optional[UUID] = None
    query_ids: Optional[list[UUID]] = None  # Support multiple query IDs
    execution_ids: Optional[list[UUID]] = None  # Support multiple execution IDs
    result_type: Optional[str] = None
    min_execution_time: Optional[int] = None
    max_execution_time: Optional[int] = None
    min_size_bytes: Optional[int] = None  # Add missing fields used in tests
    max_size_bytes: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


class StorageBackend(Enum):
    """Available storage backends."""
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    S3 = "s3"
    REDIS = "redis"
    HYBRID = "hybrid"


class CompressionType(Enum):
    """Compression algorithms."""
    NONE = "none"
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"


class SerializationFormat(Enum):
    """Serialization formats."""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    PARQUET = "parquet"


@dataclass
class StorageConfig:
    """Configuration for result storage."""
    backend: StorageBackend = StorageBackend.DATABASE
    compression: CompressionType = CompressionType.GZIP
    serialization: SerializationFormat = SerializationFormat.JSON
    max_size_mb: int = 100
    ttl_hours: int = 24
    cache_small_results: bool = True
    cache_threshold_kb: int = 10
    enable_streaming: bool = True
    chunk_size_kb: int = 64
    file_base_path: Optional[Path] = None
    s3_bucket: Optional[str] = None
    redis_prefix: str = "fraiseql_results"


@dataclass
class StorageMetrics:
    """Storage performance metrics."""
    total_results: int = 0
    total_size_bytes: int = 0
    avg_size_bytes: float = 0.0
    compression_ratio: float = 0.0
    cache_hit_rate: float = 0.0
    avg_retrieval_time_ms: float = 0.0
    avg_storage_time_ms: float = 0.0


class StorageBackendInterface(Protocol):
    """Interface for storage backend implementations."""
    
    async def store(self, key: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Store data with key and metadata."""
        ...
    
    async def retrieve(self, key: str) -> Optional[bytes]:
        """Retrieve data by key."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete data by key."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys with optional prefix."""
        ...


class DatabaseStorageBackend:
    """Database storage backend for query results."""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def store(self, key: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Store data in database."""
        try:
            await self.db_session.execute("""
                INSERT INTO result_storage (key, data, metadata, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (key) DO UPDATE SET
                    data = EXCLUDED.data,
                    metadata = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
            """, [key, data, json.dumps(metadata), datetime.now(timezone.utc)])
            
            await self.db_session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data in database: {e}")
            return False
    
    async def retrieve(self, key: str) -> Optional[bytes]:
        """Retrieve data from database."""
        try:
            result = await self.db_session.execute(
                "SELECT data FROM result_storage WHERE key = $1",
                [key]
            )
            
            return result[0]["data"] if result else None
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from database: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete data from database."""
        try:
            result = await self.db_session.execute(
                "DELETE FROM result_storage WHERE key = $1",
                [key]
            )
            await self.db_session.commit()
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to delete data from database: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in database."""
        try:
            result = await self.db_session.execute(
                "SELECT 1 FROM result_storage WHERE key = $1",
                [key]
            )
            return len(result) > 0
            
        except Exception as e:
            logger.error(f"Failed to check key existence: {e}")
            return False
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys from database."""
        try:
            if prefix:
                result = await self.db_session.execute(
                    "SELECT key FROM result_storage WHERE key LIKE $1",
                    [f"{prefix}%"]
                )
            else:
                result = await self.db_session.execute(
                    "SELECT key FROM result_storage"
                )
            
            return [row["key"] for row in result]
            
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            return []


class FileSystemStorageBackend:
    """File system storage backend for query results."""
    
    def __init__(self, base_path: Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.base_path / "_metadata"
        self.metadata_path.mkdir(exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for key."""
        # Hash key to avoid file system issues
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.base_path / f"{key_hash}.dat"
    
    def _get_metadata_path(self, key: str) -> Path:
        """Get metadata file path for key."""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.metadata_path / f"{key_hash}.json"
    
    async def store(self, key: str, data: bytes, metadata: Dict[str, Any]) -> bool:
        """Store data to file system."""
        try:
            file_path = self._get_file_path(key)
            metadata_path = self._get_metadata_path(key)
            
            # Store data
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(data)
            
            # Store metadata
            metadata_with_key = {**metadata, "original_key": key}
            async with aiofiles.open(metadata_path, "w") as f:
                await f.write(json.dumps(metadata_with_key))
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data to file system: {e}")
            return False
    
    async def retrieve(self, key: str) -> Optional[bytes]:
        """Retrieve data from file system."""
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
            
            async with aiofiles.open(file_path, "rb") as f:
                return await f.read()
            
        except Exception as e:
            logger.error(f"Failed to retrieve data from file system: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete data from file system."""
        try:
            file_path = self._get_file_path(key)
            metadata_path = self._get_metadata_path(key)
            
            deleted = False
            if file_path.exists():
                file_path.unlink()
                deleted = True
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete data from file system: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in file system."""
        file_path = self._get_file_path(key)
        return file_path.exists()
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """List keys from file system."""
        try:
            keys = []
            
            for metadata_file in self.metadata_path.glob("*.json"):
                async with aiofiles.open(metadata_file, "r") as f:
                    content = await f.read()
                    metadata = json.loads(content)
                    original_key = metadata.get("original_key", "")
                    
                    if not prefix or original_key.startswith(prefix):
                        keys.append(original_key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to list keys from file system: {e}")
            return []


class ResultStorageManager:
    """
    Manages efficient storage and retrieval of GraphQL query results.
    
    Features:
    - Multiple storage backends
    - Compression and serialization
    - Caching and TTL management
    - Streaming for large results
    - Search and analytics
    """
    
    def __init__(
        self,
        db_session,
        config: StorageConfig = None
    ):
        self.db_session = db_session
        self.config = config or StorageConfig()
        
        # Initialize storage backend
        self.backend = self._create_backend()
        
        # Result cache for small, frequently accessed results
        self._cache: Dict[str, tuple[bytes, datetime]] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Metrics tracking
        self._metrics = StorageMetrics()
    
    def _create_backend(self) -> StorageBackendInterface:
        """Create storage backend based on configuration."""
        if self.config.backend == StorageBackend.DATABASE:
            return DatabaseStorageBackend(self.db_session)
        elif self.config.backend == StorageBackend.FILE_SYSTEM:
            if not self.config.file_base_path:
                raise ValueError("file_base_path required for file system backend")
            return FileSystemStorageBackend(self.config.file_base_path)
        else:
            raise ValueError(f"Unsupported storage backend: {self.config.backend}")
    
    # Core Storage Operations
    
    async def store_result(
        self,
        execution_id: UUID,
        query_id: UUID,
        result_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store query result with automatic compression and serialization.
        
        Args:
            execution_id: Unique execution identifier
            query_id: Query that produced the result
            result_data: The actual result data
            metadata: Additional metadata
            
        Returns:
            Storage key for the result
        """
        storage_key = f"result:{execution_id}"
        start_time = datetime.now(timezone.utc)
        
        try:
            # Serialize data
            serialized_data = await self._serialize_data(result_data)
            original_size = len(serialized_data)
            
            # Compress if configured
            compressed_data = await self._compress_data(serialized_data)
            compressed_size = len(compressed_data)
            
            # Prepare metadata
            storage_metadata = {
                "execution_id": str(execution_id),
                "query_id": str(query_id),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compressed_size / original_size if original_size > 0 else 1.0,
                "serialization_format": self.config.serialization.value,
                "compression_type": self.config.compression.value,
                "stored_at": start_time.isoformat(),
                "ttl_hours": self.config.ttl_hours,
                **(metadata or {})
            }
            
            # Store in backend
            success = await self.backend.store(storage_key, compressed_data, storage_metadata)
            
            if not success:
                raise Exception("Backend storage failed")
            
            # Cache small results
            if (self.config.cache_small_results and 
                compressed_size < self.config.cache_threshold_kb * 1024):
                self._cache[storage_key] = (compressed_data, start_time)
            
            # Update metrics
            self._update_storage_metrics(original_size, compressed_size, start_time)
            
            # Store result record in database
            await self._store_result_record(execution_id, query_id, storage_key, storage_metadata)
            
            logger.info(f"Stored result {storage_key}, compressed {original_size} -> {compressed_size} bytes")
            
            return storage_key
            
        except Exception as e:
            logger.error(f"Failed to store result {execution_id}: {e}")
            raise
    
    async def retrieve_result(
        self,
        storage_key: str,
        stream: bool = False
    ) -> Optional[Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]]:
        """
        Retrieve query result with automatic decompression and deserialization.
        
        Args:
            storage_key: Key to retrieve
            stream: Whether to stream large results
            
        Returns:
            Deserialized result data or async iterator for streaming
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Check cache first
            if storage_key in self._cache:
                compressed_data, cached_at = self._cache[storage_key]
                
                # Check TTL
                if (datetime.now(timezone.utc) - cached_at).total_seconds() < self.config.ttl_hours * 3600:
                    self._cache_hits += 1
                    
                    # Decompress and deserialize
                    serialized_data = await self._decompress_data(compressed_data)
                    result_data = await self._deserialize_data(serialized_data)
                    
                    self._update_retrieval_metrics(start_time, cache_hit=True)
                    return result_data
                else:
                    # Remove expired cache entry
                    del self._cache[storage_key]
            
            self._cache_misses += 1
            
            # Retrieve from backend
            compressed_data = await self.backend.retrieve(storage_key)
            if not compressed_data:
                return None
            
            # Decompress
            serialized_data = await self._decompress_data(compressed_data)
            
            # Handle streaming for large results
            if stream and len(serialized_data) > self.config.chunk_size_kb * 1024:
                return self._stream_deserialize(serialized_data)
            
            # Regular deserialization
            result_data = await self._deserialize_data(serialized_data)
            
            # Cache if small enough
            if (self.config.cache_small_results and 
                len(compressed_data) < self.config.cache_threshold_kb * 1024):
                self._cache[storage_key] = (compressed_data, datetime.now(timezone.utc))
            
            self._update_retrieval_metrics(start_time, cache_hit=False)
            
            return result_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve result {storage_key}: {e}")
            return None
    
    async def delete_result(self, storage_key: str) -> bool:
        """Delete a stored result."""
        try:
            # Remove from cache
            if storage_key in self._cache:
                del self._cache[storage_key]
            
            # Delete from backend
            success = await self.backend.delete(storage_key)
            
            # Delete result record
            await self.db_session.execute(
                "DELETE FROM query_results WHERE storage_key = $1",
                [storage_key]
            )
            await self.db_session.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete result {storage_key}: {e}")
            return False
    
    # Serialization and Compression
    
    async def _serialize_data(self, data: Dict[str, Any]) -> bytes:
        """Serialize data based on configuration."""
        if self.config.serialization == SerializationFormat.JSON:
            return json.dumps(data, default=str).encode('utf-8')
        elif self.config.serialization == SerializationFormat.PICKLE:
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported serialization format: {self.config.serialization}")
    
    async def _deserialize_data(self, data: bytes) -> Dict[str, Any]:
        """Deserialize data based on configuration."""
        if self.config.serialization == SerializationFormat.JSON:
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization == SerializationFormat.PICKLE:
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported serialization format: {self.config.serialization}")
    
    async def _compress_data(self, data: bytes) -> bytes:
        """Compress data based on configuration."""
        if self.config.compression == CompressionType.NONE:
            return data
        elif self.config.compression == CompressionType.GZIP:
            return gzip.compress(data)
        else:
            raise ValueError(f"Unsupported compression type: {self.config.compression}")
    
    async def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data based on configuration."""
        if self.config.compression == CompressionType.NONE:
            return data
        elif self.config.compression == CompressionType.GZIP:
            return gzip.decompress(data)
        else:
            raise ValueError(f"Unsupported compression type: {self.config.compression}")
    
    async def _stream_deserialize(self, data: bytes) -> AsyncIterator[Dict[str, Any]]:
        """Stream deserialize large data in chunks."""
        # For now, just yield the full data
        # In a real implementation, you might stream JSON parsing
        result = await self._deserialize_data(data)
        yield result
    
    # Search and Analytics
    
    async def search_results(
        self,
        filter_params: ResultSearchFilter
    ) -> List[QueryResult]:
        """Search stored results with filtering."""
        query_parts = ["SELECT * FROM query_results WHERE 1=1"]
        params = []
        param_counter = 0
        
        # Query ID filter
        if filter_params.query_ids:
            param_counter += 1
            query_parts.append(f"AND query_id = ANY(${param_counter})")
            params.append(filter_params.query_ids)
        
        # Execution ID filter
        if filter_params.execution_ids:
            param_counter += 1
            query_parts.append(f"AND execution_id = ANY(${param_counter})")
            params.append(filter_params.execution_ids)
        
        # Date range
        if filter_params.created_after:
            param_counter += 1
            query_parts.append(f"AND created_at >= ${param_counter}")
            params.append(filter_params.created_after)
        
        if filter_params.created_before:
            param_counter += 1
            query_parts.append(f"AND created_at <= ${param_counter}")
            params.append(filter_params.created_before)
        
        # Size range
        if filter_params.min_size_bytes:
            param_counter += 1
            query_parts.append(f"AND metadata->>'original_size' >= ${param_counter}")
            params.append(str(filter_params.min_size_bytes))
        
        if filter_params.max_size_bytes:
            param_counter += 1
            query_parts.append(f"AND metadata->>'original_size' <= ${param_counter}")
            params.append(str(filter_params.max_size_bytes))
        
        # Pagination
        query_parts.append("ORDER BY created_at DESC")
        
        param_counter += 1
        query_parts.append(f"LIMIT ${param_counter}")
        params.append(filter_params.limit)
        
        param_counter += 1
        query_parts.append(f"OFFSET ${param_counter}")
        params.append(filter_params.offset)
        
        final_query = " ".join(query_parts)
        results = await self.db_session.execute(final_query, params)
        
        return [QueryResult.from_dict(row) for row in results]
    
    async def get_storage_analytics(
        self,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """Get storage analytics and insights."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Query database for analytics
        analytics = await self.db_session.execute("""
            SELECT 
                COUNT(*) as total_results,
                SUM((metadata->>'original_size')::bigint) as total_original_size,
                SUM((metadata->>'compressed_size')::bigint) as total_compressed_size,
                AVG((metadata->>'original_size')::bigint) as avg_original_size,
                AVG((metadata->>'compressed_size')::bigint) as avg_compressed_size,
                AVG((metadata->>'compression_ratio')::float) as avg_compression_ratio,
                COUNT(DISTINCT query_id) as unique_queries
            FROM query_results
            WHERE created_at >= $1
        """, [cutoff_date])
        
        if analytics:
            stats = analytics[0]
            
            # Calculate compression savings
            total_original = stats.get('total_original_size', 0) or 0
            total_compressed = stats.get('total_compressed_size', 0) or 0
            space_saved = total_original - total_compressed
            space_saved_pct = (space_saved / total_original * 100) if total_original > 0 else 0
            
            return {
                "period_days": days_back,
                "total_results": stats.get('total_results', 0),
                "unique_queries": stats.get('unique_queries', 0),
                "storage_usage": {
                    "total_original_bytes": total_original,
                    "total_compressed_bytes": total_compressed,
                    "space_saved_bytes": space_saved,
                    "space_saved_percentage": space_saved_pct,
                    "avg_compression_ratio": stats.get('avg_compression_ratio', 1.0)
                },
                "size_metrics": {
                    "avg_original_size_bytes": stats.get('avg_original_size', 0) or 0,
                    "avg_compressed_size_bytes": stats.get('avg_compressed_size', 0) or 0
                },
                "cache_metrics": {
                    "hit_rate": self._get_cache_hit_rate(),
                    "cache_size": len(self._cache),
                    "total_hits": self._cache_hits,
                    "total_misses": self._cache_misses
                }
            }
        
        return {"error": "No data available"}
    
    # Utility Methods
    
    async def _store_result_record(
        self,
        execution_id: UUID,
        query_id: UUID,
        storage_key: str,
        metadata: Dict[str, Any]
    ):
        """Store result record in database."""
        result_record = QueryResult(
            pk_query_result=uuid4(),
            fk_execution=execution_id,
            fk_query=query_id,
            result_hash=storage_key,
            original_size_bytes=metadata.get('original_size', 0),
            compressed_size_bytes=metadata.get('compressed_size', 0),
            search_metadata=metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db_session.add(result_record)
        await self.db_session.commit()
    
    def _update_storage_metrics(
        self,
        original_size: int,
        compressed_size: int,
        start_time: datetime
    ):
        """Update storage performance metrics."""
        self._metrics.total_results += 1
        self._metrics.total_size_bytes += original_size
        
        # Update averages
        self._metrics.avg_size_bytes = (
            self._metrics.total_size_bytes / self._metrics.total_results
        )
        
        if original_size > 0:
            compression_ratio = compressed_size / original_size
            # Moving average for compression ratio
            self._metrics.compression_ratio = (
                (self._metrics.compression_ratio * (self._metrics.total_results - 1) + compression_ratio) /
                self._metrics.total_results
            )
        
        # Storage time
        storage_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._metrics.avg_storage_time_ms = (
            (self._metrics.avg_storage_time_ms * (self._metrics.total_results - 1) + storage_time_ms) /
            self._metrics.total_results
        )
    
    def _update_retrieval_metrics(self, start_time: datetime, cache_hit: bool):
        """Update retrieval performance metrics."""
        retrieval_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Update average retrieval time
        total_retrievals = self._cache_hits + self._cache_misses
        if total_retrievals > 0:
            self._metrics.avg_retrieval_time_ms = (
                (self._metrics.avg_retrieval_time_ms * (total_retrievals - 1) + retrieval_time_ms) /
                total_retrievals
            )
        
        # Update cache hit rate
        self._metrics.cache_hit_rate = self._get_cache_hit_rate()
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self._cache_hits + self._cache_misses
        return (self._cache_hits / total_requests * 100) if total_requests > 0 else 0.0
    
    async def cleanup_expired_results(self) -> int:
        """Clean up expired results based on TTL."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.config.ttl_hours)
        
        # Get expired result keys
        expired_results = await self.db_session.execute("""
            SELECT storage_key FROM query_results 
            WHERE created_at < $1
        """, [cutoff_time])
        
        deleted_count = 0
        
        for row in expired_results:
            storage_key = row["storage_key"]
            if await self.delete_result(storage_key):
                deleted_count += 1
        
        # Clean cache of expired entries
        expired_cache_keys = []
        for key, (data, cached_at) in self._cache.items():
            if (datetime.now(timezone.utc) - cached_at).total_seconds() > self.config.ttl_hours * 3600:
                expired_cache_keys.append(key)
        
        for key in expired_cache_keys:
            del self._cache[key]
        
        logger.info(f"Cleaned up {deleted_count} expired results and {len(expired_cache_keys)} cache entries")
        
        return deleted_count
    
    async def get_metrics(self) -> StorageMetrics:
        """Get current storage metrics."""
        return self._metrics
"""Result storage models."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class QueryResult(Base, TimestampMixin):
    """Query result storage model."""

    __tablename__ = "tb_query_result"

    pk_query_result: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query: Mapped[UUID] = mapped_column(nullable=False)  # Foreign key to Query
    fk_execution: Mapped[UUID] = mapped_column(nullable=False)  # Foreign key to Execution
    result_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256 hash
    result_data: Mapped[dict[str, Any]] = mapped_column(default=dict)
    compression_type: Mapped[str] = mapped_column(String(20), default="none")
    original_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    compressed_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    storage_backend: Mapped[str] = mapped_column(String(20), default="database")
    storage_path: Mapped[str | None] = mapped_column(Text)  # Path for file/S3 storage
    ttl_expires_at: Mapped[datetime | None] = mapped_column()
    search_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueryResult":
        """Create QueryResult instance from dictionary."""
        return cls(
            pk_query_result=data.get("pk_query_result") or data.get("id"),
            fk_query=data.get("fk_query") or data.get("query_id"),
            fk_execution=data.get("fk_execution") or data.get("execution_id"),
            result_hash=data.get("result_hash"),
            result_data=data.get("result_data", {}),
            compression_type=data.get("compression_type", "none"),
            original_size_bytes=data.get("original_size_bytes", 0),
            compressed_size_bytes=data.get("compressed_size_bytes", 0),
            storage_backend=data.get("storage_backend", "database"),
            storage_path=data.get("storage_path") or data.get("storage_key"),
            ttl_expires_at=data.get("ttl_expires_at"),
            search_metadata=data.get("search_metadata") or data.get("metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert QueryResult to dictionary."""
        return {
            "pk_query_result": self.pk_query_result,
            "fk_query": self.fk_query,
            "fk_execution": self.fk_execution,
            "result_hash": self.result_hash,
            "result_data": self.result_data,
            "compression_type": self.compression_type,
            "original_size_bytes": self.original_size_bytes,
            "compressed_size_bytes": self.compressed_size_bytes,
            "storage_backend": self.storage_backend,
            "storage_path": self.storage_path,
            "ttl_expires_at": self.ttl_expires_at,
            "search_metadata": self.search_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ResultMetadata(Base, TimestampMixin):
    """Result metadata for analytics and search."""

    __tablename__ = "tb_result_metadata"

    pk_result_metadata: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query_result: Mapped[UUID] = mapped_column(nullable=False)  # Foreign key to QueryResult
    result_type: Mapped[str] = mapped_column(String(50), nullable=False)  # success, error, partial
    field_count: Mapped[int] = mapped_column(Integer, default=0)
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    complexity_score: Mapped[float | None] = mapped_column(Float)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    cache_hit: Mapped[bool] = mapped_column(default=False)
    performance_notes: Mapped[str | None] = mapped_column(Text)
    analytics_data: Mapped[dict[str, Any]] = mapped_column(default=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResultMetadata":
        """Create ResultMetadata instance from dictionary."""
        return cls(
            pk_result_metadata=data.get("pk_result_metadata"),
            fk_query_result=data["fk_query_result"],
            result_type=data["result_type"],
            field_count=data.get("field_count", 0),
            record_count=data.get("record_count", 0),
            complexity_score=data.get("complexity_score"),
            execution_time_ms=data.get("execution_time_ms", 0),
            cache_hit=data.get("cache_hit", False),
            performance_notes=data.get("performance_notes"),
            analytics_data=data.get("analytics_data", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert ResultMetadata to dictionary."""
        return {
            "pk_result_metadata": self.pk_result_metadata,
            "fk_query_result": self.fk_query_result,
            "result_type": self.result_type,
            "field_count": self.field_count,
            "record_count": self.record_count,
            "complexity_score": self.complexity_score,
            "execution_time_ms": self.execution_time_ms,
            "cache_hit": self.cache_hit,
            "performance_notes": self.performance_notes,
            "analytics_data": self.analytics_data,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

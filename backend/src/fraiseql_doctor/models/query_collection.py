"""Query collection and metadata models."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class QueryCollection(Base, TimestampMixin):
    """Query collection model for organizing related queries."""

    __tablename__ = "tb_query_collection"

    pk_query_collection: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships - if needed
    # queries = relationship("Query", back_populates="collection")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueryCollection":
        """Create QueryCollection instance from dictionary."""
        return cls(
            pk_query_collection=data.get("pk_query_collection"),
            name=data["name"],
            description=data.get("description"),
            tags=data.get("tags", {}),
            created_by=data["created_by"],
            collection_metadata=data.get("collection_metadata", {}),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert QueryCollection to dictionary."""
        return {
            "pk_query_collection": self.pk_query_collection,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "created_by": self.created_by,
            "collection_metadata": self.collection_metadata,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class QueryMetadata(Base, TimestampMixin):
    """Query metadata for tracking execution history and performance."""

    __tablename__ = "tb_query_metadata"

    pk_query_metadata: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    pk_query: Mapped[UUID] = mapped_column(nullable=False)  # Foreign key to Query
    execution_count: Mapped[int] = mapped_column(default=0)
    last_executed: Mapped[datetime | None] = mapped_column()
    average_execution_time: Mapped[float | None] = mapped_column()
    success_rate: Mapped[float | None] = mapped_column()
    complexity_score: Mapped[float | None] = mapped_column()
    performance_notes: Mapped[str | None] = mapped_column(Text)
    query_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueryMetadata":
        """Create QueryMetadata instance from dictionary."""
        return cls(
            pk_query_metadata=data.get("pk_query_metadata"),
            pk_query=data["pk_query"],
            execution_count=data.get("execution_count", 0),
            last_executed=data.get("last_executed"),
            average_execution_time=data.get("average_execution_time"),
            success_rate=data.get("success_rate"),
            complexity_score=data.get("complexity_score"),
            performance_notes=data.get("performance_notes"),
            query_metadata=data.get("query_metadata", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert QueryMetadata to dictionary."""
        return {
            "pk_query_metadata": self.pk_query_metadata,
            "pk_query": self.pk_query,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed,
            "average_execution_time": self.average_execution_time,
            "success_rate": self.success_rate,
            "complexity_score": self.complexity_score,
            "performance_notes": self.performance_notes,
            "query_metadata": self.query_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

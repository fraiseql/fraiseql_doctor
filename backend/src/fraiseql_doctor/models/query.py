"""Query storage model."""
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Query(Base, TimestampMixin):
    """Stored GraphQL/FraiseQL query model."""
    __tablename__ = "tb_query"

    pk_query: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict[str, Any]] = mapped_column(default=dict)
    expected_complexity_score: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255))
    query_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # Relationships (using string references to avoid circular imports)
    executions = relationship("Execution", back_populates="query", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="query", cascade="all, delete-orphan")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Query":
        """Create Query instance from dictionary."""
        # Handle both database field names and test field names
        query_text = data.get("query_text") or data.get("content", "")
        pk_query = data.get("pk_query") or data.get("id")
        
        return cls(
            pk_query=pk_query,
            name=data["name"],
            description=data.get("description"),
            query_text=query_text,
            variables=data.get("variables", {}),
            expected_complexity_score=data.get("expected_complexity_score"),
            tags=data.get("tags", []),
            is_active=data.get("is_active", True),
            created_by=data.get("created_by"),
            query_metadata=data.get("query_metadata", data.get("metadata", {})),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Query to dictionary."""
        return {
            "pk_query": self.pk_query,
            "name": self.name,
            "description": self.description,
            "query_text": self.query_text,
            "variables": self.variables,
            "expected_complexity_score": self.expected_complexity_score,
            "tags": self.tags,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "query_metadata": self.query_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
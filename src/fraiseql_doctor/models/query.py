"""Query storage model."""
from typing import Any
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
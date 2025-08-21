"""Query execution tracking model."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Execution(Base):
    """Query execution history model."""

    __tablename__ = "query_executions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    query_id: Mapped[UUID] = mapped_column(ForeignKey("queries.id", ondelete="CASCADE"))
    endpoint_id: Mapped[UUID] = mapped_column(ForeignKey("endpoints.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pending, success, error, timeout
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    complexity_score: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_details: Mapped[dict[str, Any] | None] = mapped_column()
    response_data: Mapped[dict[str, Any] | None] = mapped_column()
    variables: Mapped[dict[str, Any]] = mapped_column(default=dict)
    execution_context: Mapped[dict[str, Any]] = mapped_column(default=dict)
    operation_name: Mapped[str | None] = mapped_column(String(255))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    trace_id: Mapped[str | None] = mapped_column(String(255))
    span_id: Mapped[str | None] = mapped_column(String(255))
    triggered_by: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships disabled temporarily for API testing
    # query = relationship("Query", back_populates="executions")
    # endpoint = relationship("Endpoint", back_populates="executions")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Execution":
        """Create Execution instance from dictionary."""
        return cls(
            id=data.get("id"),
            query_id=data["query_id"],
            endpoint_id=data["endpoint_id"],
            started_at=data["started_at"],
            completed_at=data.get("completed_at"),
            status=data["status"],
            response_time_ms=data.get("response_time_ms"),
            complexity_score=data.get("complexity_score"),
            error_message=data.get("error_message"),
            error_details=data.get("error_details"),
            response_data=data.get("response_data"),
            variables=data.get("variables", {}),
            execution_context=data.get("execution_context", {}),
            operation_name=data.get("operation_name"),
            user_agent=data.get("user_agent"),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            triggered_by=data.get("triggered_by"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

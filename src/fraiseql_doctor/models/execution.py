"""Query execution tracking model."""
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Execution(Base):
    """Query execution history model."""
    __tablename__ = "tb_execution"

    pk_execution: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query: Mapped[UUID] = mapped_column(ForeignKey("tb_query.pk_query", ondelete="CASCADE"))
    fk_endpoint: Mapped[UUID] = mapped_column(ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"))
    execution_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    execution_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, success, error, timeout
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    response_size_bytes: Mapped[int | None] = mapped_column(Integer)
    actual_complexity_score: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(50))
    response_data: Mapped[dict[str, Any] | None] = mapped_column()
    variables_used: Mapped[dict[str, Any]] = mapped_column(default=dict)
    execution_context: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships (using string references to avoid circular imports)
    query = relationship("Query", back_populates="executions")
    endpoint = relationship("Endpoint", back_populates="executions")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Execution":
        """Create Execution instance from dictionary."""
        return cls(
            pk_execution=data.get("pk_execution"),
            fk_query=data["fk_query"],
            fk_endpoint=data["fk_endpoint"],
            execution_start=data["execution_start"],
            execution_end=data.get("execution_end"),
            status=data["status"],
            response_time_ms=data.get("response_time_ms"),
            response_size_bytes=data.get("response_size_bytes"),
            actual_complexity_score=data.get("actual_complexity_score"),
            error_message=data.get("error_message"),
            error_code=data.get("error_code"),
            response_data=data.get("response_data"),
            variables_used=data.get("variables_used", {}),
            execution_context=data.get("execution_context", {}),
            created_at=data.get("created_at")
        )
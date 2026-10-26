"""Health check tracking model."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class HealthCheck(Base):
    """Endpoint health check history model."""

    __tablename__ = "tb_health_check"

    pk_health_check: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_endpoint: Mapped[UUID] = mapped_column(
        ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE")
    )
    check_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    available_operations: Mapped[list[str]] = mapped_column(default=list)
    schema_hash: Mapped[str | None] = mapped_column(String(64))
    check_metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # Relationships (using string references to avoid circular imports)
    endpoint = relationship("Endpoint", back_populates="health_checks")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HealthCheck":
        """Create HealthCheck instance from dictionary."""
        return cls(
            pk_health_check=data.get("pk_health_check"),
            fk_endpoint=data["fk_endpoint"],
            check_time=data.get("check_time", datetime.utcnow()),
            is_healthy=data["is_healthy"],
            response_time_ms=data.get("response_time_ms"),
            error_message=data.get("error_message"),
            available_operations=data.get("available_operations", []),
            schema_hash=data.get("schema_hash"),
            check_metadata=data.get("check_metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert HealthCheck to dictionary."""
        return {
            "pk_health_check": self.pk_health_check,
            "fk_endpoint": self.fk_endpoint,
            "check_time": self.check_time,
            "is_healthy": self.is_healthy,
            "response_time_ms": self.response_time_ms,
            "error_message": self.error_message,
            "available_operations": self.available_operations,
            "schema_hash": self.schema_hash,
            "check_metadata": self.check_metadata,
        }

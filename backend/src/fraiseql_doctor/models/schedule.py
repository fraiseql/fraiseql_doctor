"""Query scheduling model."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Schedule(Base, TimestampMixin):
    """Query scheduling model."""

    __tablename__ = "tb_schedule"

    pk_schedule: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query: Mapped[UUID] = mapped_column(ForeignKey("tb_query.pk_query", ondelete="CASCADE"))
    fk_endpoint: Mapped[UUID] = mapped_column(
        ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    variables_override: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # Relationships (using string references to avoid circular imports)
    query = relationship("Query", back_populates="schedules")
    endpoint = relationship("Endpoint", back_populates="schedules")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Schedule":
        """Create Schedule instance from dictionary."""
        return cls(
            pk_schedule=data.get("pk_schedule"),
            fk_query=data["fk_query"],
            fk_endpoint=data["fk_endpoint"],
            name=data["name"],
            cron_expression=data["cron_expression"],
            is_active=data.get("is_active", True),
            next_run=data.get("next_run"),
            last_run=data.get("last_run"),
            variables_override=data.get("variables_override", {}),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Schedule to dictionary."""
        return {
            "pk_schedule": self.pk_schedule,
            "fk_query": self.fk_query,
            "fk_endpoint": self.fk_endpoint,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "is_active": self.is_active,
            "next_run": self.next_run,
            "last_run": self.last_run,
            "variables_override": self.variables_override,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

"""Query scheduling model."""
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Schedule(Base, TimestampMixin):
    """Query scheduling model."""
    __tablename__ = "tb_schedule"

    pk_schedule: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query: Mapped[UUID] = mapped_column(ForeignKey("tb_query.pk_query", ondelete="CASCADE"))
    fk_endpoint: Mapped[UUID] = mapped_column(ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    variables_override: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # Relationships (using string references to avoid circular imports)
    query = relationship("Query", back_populates="schedules")
    endpoint = relationship("Endpoint", back_populates="schedules")
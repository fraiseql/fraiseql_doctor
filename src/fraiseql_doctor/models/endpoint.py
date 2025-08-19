"""Endpoint configuration model."""
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Endpoint(Base, TimestampMixin):
    """GraphQL endpoint configuration model."""
    __tablename__ = "tb_endpoint"

    pk_endpoint: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(50), default="none")
    auth_config: Mapped[dict[str, Any]] = mapped_column(default=dict)
    headers: Mapped[dict[str, Any]] = mapped_column(default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships (using string references to avoid circular imports)
    executions = relationship("Execution", back_populates="endpoint", cascade="all, delete-orphan")
    health_checks = relationship("HealthCheck", back_populates="endpoint", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="endpoint", cascade="all, delete-orphan")
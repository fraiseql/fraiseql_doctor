"""Endpoint configuration model."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String
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
    health_checks = relationship(
        "HealthCheck", back_populates="endpoint", cascade="all, delete-orphan"
    )
    schedules = relationship("Schedule", back_populates="endpoint", cascade="all, delete-orphan")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Endpoint":
        """Create Endpoint instance from dictionary."""
        return cls(
            pk_endpoint=data.get("pk_endpoint"),
            name=data["name"],
            url=data["url"],
            auth_type=data.get("auth_type", "none"),
            auth_config=data.get("auth_config", {}),
            headers=data.get("headers", {}),
            timeout_seconds=data.get("timeout_seconds", 30),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 1),
            is_active=data.get("is_active", True),
            last_health_check=data.get("last_health_check"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Endpoint to dictionary."""
        return {
            "pk_endpoint": self.pk_endpoint,
            "name": self.name,
            "url": self.url,
            "auth_type": self.auth_type,
            "auth_config": self.auth_config,
            "headers": self.headers,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "is_active": self.is_active,
            "last_health_check": self.last_health_check,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

"""Endpoint model for storing GraphQL endpoint configurations."""

import enum
from typing import Any

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    ActiveMixin,
    BaseModel,
    NameDescriptionMixin,
    UserTrackingMixin,
)


class AuthType(enum.Enum):
    """Authentication types for GraphQL endpoints."""

    NONE = "none"
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"


class Endpoint(BaseModel, NameDescriptionMixin, ActiveMixin, UserTrackingMixin):
    """GraphQL endpoint configuration."""

    __tablename__ = "endpoints"

    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    auth_type: Mapped[AuthType] = mapped_column(
        Enum(AuthType), default=AuthType.NONE, nullable=False
    )
    auth_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Health check configuration
    health_check_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    health_check_interval: Mapped[int] = mapped_column(Integer, default=300, nullable=False)  # seconds
    
    # Statistics
    total_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_response_time_ms: Mapped[float | None] = mapped_column(nullable=True)
    
    # Circuit breaker settings
    failure_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    circuit_breaker_timeout: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # seconds
    is_circuit_open: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Additional metadata
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    query_executions = relationship("QueryExecution", back_populates="endpoint")
    health_checks = relationship("HealthCheck", back_populates="endpoint")
    scheduled_queries = relationship("ScheduledQuery", back_populates="endpoint")

    def __repr__(self) -> str:
        """String representation of the endpoint."""
        return f"<Endpoint(name='{self.name}', url='{self.url}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_requests == 0:
            return 100.0
        return ((self.total_requests - self.total_failures) / self.total_requests) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if endpoint is considered healthy."""
        return self.is_active and not self.is_circuit_open and self.success_rate > 50

    def update_stats(self, success: bool, response_time_ms: float) -> None:
        """Update endpoint statistics."""
        self.total_requests += 1
        if not success:
            self.total_failures += 1

        # Update rolling average response time
        if self.avg_response_time_ms is None:
            self.avg_response_time_ms = response_time_ms
        else:
            # Simple moving average - in production, consider using a more sophisticated approach
            weight = 0.1  # Weight for new measurement
            self.avg_response_time_ms = (
                self.avg_response_time_ms * (1 - weight) + response_time_ms * weight
            )

    def should_open_circuit(self) -> bool:
        """Check if circuit breaker should be opened."""
        if self.total_requests < self.failure_threshold:
            return False
        
        recent_failure_rate = self.total_failures / self.total_requests
        return recent_failure_rate >= 0.5  # 50% failure rate
"""Execution and health check models for tracking query results."""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class ExecutionStatus(enum.Enum):
    """Status of query execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class HealthStatus(enum.Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class QueryExecution(BaseModel):
    """Record of a query execution."""

    __tablename__ = "query_executions"

    # Foreign keys
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("endpoints.id"), nullable=False
    )

    # Execution details
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False
    )
    variables: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Results
    response_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Metadata
    complexity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    operation_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Trace information for debugging
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    span_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Context
    execution_context: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Execution source
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 'manual', 'scheduled', 'health_check'

    # Relationships
    query = relationship("Query", back_populates="executions")
    endpoint = relationship("Endpoint", back_populates="query_executions")

    def __repr__(self) -> str:
        """String representation of the execution."""
        return f"<QueryExecution(id={self.id}, status='{self.status.value}')>"

    @property
    def duration_ms(self) -> float | None:
        """Calculate execution duration in milliseconds."""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    @property
    def is_successful(self) -> bool:
        """Check if execution was successful."""
        return self.status == ExecutionStatus.SUCCESS

    def mark_completed(self, status: ExecutionStatus, response_time_ms: float | None = None) -> None:
        """Mark execution as completed with given status."""
        self.status = status
        self.completed_at = func.now()
        if response_time_ms is not None:
            self.response_time_ms = response_time_ms

    def add_error(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Add error information to the execution."""
        self.error_message = message
        self.error_details = details or {}
        if self.status == ExecutionStatus.PENDING or self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED


class HealthCheck(BaseModel):
    """Health check record for endpoints."""

    __tablename__ = "health_checks"

    # Foreign key
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("endpoints.id"), nullable=False
    )

    # Health status
    status: Mapped[HealthStatus] = mapped_column(
        Enum(HealthStatus), default=HealthStatus.UNKNOWN, nullable=False
    )
    
    # Timing
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Health details
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metrics
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Additional context
    check_type: Mapped[str] = mapped_column(String(50), default="basic", nullable=False)  # 'basic', 'introspection', 'custom'
    check_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    endpoint = relationship("Endpoint", back_populates="health_checks")

    def __repr__(self) -> str:
        """String representation of the health check."""
        return f"<HealthCheck(endpoint_id={self.endpoint_id}, status='{self.status.value}')>"

    @property
    def is_healthy(self) -> bool:
        """Check if this health check indicates healthy status."""
        return self.status == HealthStatus.HEALTHY

    def set_healthy(self, response_time_ms: float, details: dict[str, Any] | None = None) -> None:
        """Mark health check as healthy."""
        self.status = HealthStatus.HEALTHY
        self.response_time_ms = response_time_ms
        self.details = details or {}
        self.error_message = None

    def set_unhealthy(self, error_message: str, details: dict[str, Any] | None = None) -> None:
        """Mark health check as unhealthy."""
        self.status = HealthStatus.UNHEALTHY
        self.error_message = error_message
        self.details = details or {}

    def set_degraded(self, reason: str, response_time_ms: float, details: dict[str, Any] | None = None) -> None:
        """Mark health check as degraded."""
        self.status = HealthStatus.DEGRADED
        self.response_time_ms = response_time_ms
        self.error_message = reason
        self.details = details or {}
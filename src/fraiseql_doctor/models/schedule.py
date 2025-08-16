"""Scheduling models for automated query execution."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any

from croniter import croniter
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import (
    ActiveMixin,
    BaseModel,
    NameDescriptionMixin,
    UserTrackingMixin,
)


class ScheduleStatus(enum.Enum):
    """Status of scheduled queries."""

    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ERROR = "error"


class ScheduledQuery(BaseModel, NameDescriptionMixin, ActiveMixin, UserTrackingMixin):
    """Scheduled query execution configuration."""

    __tablename__ = "scheduled_queries"

    # Foreign keys
    query_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("queries.id"), nullable=False
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("endpoints.id"), nullable=False
    )

    # Schedule configuration
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    
    # Execution configuration
    variables: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    
    # Status and control
    status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus), default=ScheduleStatus.ACTIVE, nullable=False
    )
    
    # Timing
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Failure handling
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_consecutive_failures: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    failure_threshold_reached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Statistics
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Notifications
    notify_on_failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notify_on_success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notification_config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    
    # Additional metadata
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Last execution details
    last_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    query = relationship("Query", back_populates="scheduled_queries")
    endpoint = relationship("Endpoint", back_populates="scheduled_queries")

    def __repr__(self) -> str:
        """String representation of the scheduled query."""
        return f"<ScheduledQuery(name='{self.name}', cron='{self.cron_expression}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_runs == 0:
            return 100.0
        return (self.successful_runs / self.total_runs) * 100

    @property
    def is_due(self) -> bool:
        """Check if the scheduled query is due to run."""
        if not self.is_active or self.status != ScheduleStatus.ACTIVE:
            return False
        
        if self.next_run_at is None:
            return True  # Never run before
        
        now = datetime.now(timezone.utc)
        return now >= self.next_run_at

    @property
    def is_healthy(self) -> bool:
        """Check if the schedule is in a healthy state."""
        return (
            self.is_active
            and self.status == ScheduleStatus.ACTIVE
            and not self.failure_threshold_reached
            and self.consecutive_failures < self.max_consecutive_failures
        )

    def validate_cron_expression(self) -> bool:
        """Validate the cron expression."""
        try:
            croniter(self.cron_expression)
            return True
        except Exception:
            return False

    def calculate_next_run(self, base_time: datetime | None = None) -> datetime:
        """Calculate the next run time based on cron expression."""
        if base_time is None:
            base_time = datetime.now(timezone.utc)
        
        cron = croniter(self.cron_expression, base_time)
        return cron.get_next(datetime)

    def update_next_run(self) -> None:
        """Update the next_run_at timestamp."""
        self.next_run_at = self.calculate_next_run()

    def record_execution(self, success: bool, execution_id: uuid.UUID | None = None, error_message: str | None = None) -> None:
        """Record the result of a scheduled execution."""
        self.total_runs += 1
        self.last_run_at = datetime.now(timezone.utc)
        self.last_execution_id = execution_id
        
        if success:
            self.successful_runs += 1
            self.consecutive_failures = 0
            self.last_success_at = self.last_run_at
            self.last_error_message = None
            self.failure_threshold_reached = False
        else:
            self.failed_runs += 1
            self.consecutive_failures += 1
            self.last_error_message = error_message
            
            # Check if failure threshold is reached
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.failure_threshold_reached = True
                self.status = ScheduleStatus.ERROR

        # Update next run time
        self.update_next_run()

    def reset_failures(self) -> None:
        """Reset failure counters and re-enable the schedule."""
        self.consecutive_failures = 0
        self.failure_threshold_reached = False
        self.last_error_message = None
        if self.status == ScheduleStatus.ERROR:
            self.status = ScheduleStatus.ACTIVE

    def pause(self) -> None:
        """Pause the scheduled query."""
        if self.status == ScheduleStatus.ACTIVE:
            self.status = ScheduleStatus.PAUSED

    def resume(self) -> None:
        """Resume the scheduled query."""
        if self.status == ScheduleStatus.PAUSED:
            self.status = ScheduleStatus.ACTIVE
            self.update_next_run()

    def disable(self) -> None:
        """Disable the scheduled query."""
        self.status = ScheduleStatus.DISABLED
        self.is_active = False
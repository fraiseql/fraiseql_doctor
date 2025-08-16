"""Database models for FraiseQL Doctor."""

from .base import Base, BaseModel, TimestampMixin, UUIDMixin
from .endpoint import AuthType, Endpoint
from .execution import ExecutionStatus, HealthCheck, HealthStatus, QueryExecution
from .query import Query, QueryType
from .schedule import ScheduledQuery, ScheduleStatus

__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
    # Endpoint models
    "Endpoint",
    "AuthType",
    # Query models
    "Query",
    "QueryType",
    # Execution models
    "QueryExecution",
    "ExecutionStatus",
    "HealthCheck",
    "HealthStatus",
    # Schedule models
    "ScheduledQuery",
    "ScheduleStatus",
]

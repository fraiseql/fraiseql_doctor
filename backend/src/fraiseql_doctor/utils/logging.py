"""Production-grade structured logging infrastructure for FraiseQL Doctor.

Provides:
- JSON-formatted logs for production
- Configurable log levels via environment variables
- Performance metrics logging
- Error context preservation
- Structured fields (timestamp, level, component, trace_id)
- Security-aware logging (credential masking)
"""

import json
import logging
import logging.config
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from functools import wraps
from typing import Any


class SecurityFilter(logging.Filter):
    """Filter to mask sensitive information in logs."""

    SENSITIVE_KEYS = {
        "password",
        "token",
        "secret",
        "key",
        "credential",
        "auth",
        "authorization",
        "cookie",
        "session",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Mask sensitive data in log record."""
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Basic masking - replace sensitive patterns
            for key in self.SENSITIVE_KEYS:
                if key in record.msg.lower():
                    record.msg = record.msg.replace(key, f"{key}=***")

        # Mask sensitive data in record attributes
        for attr_name in dir(record):
            if not attr_name.startswith("_"):
                attr_value = getattr(record, attr_name, None)
                if isinstance(attr_value, (str, dict)):
                    setattr(record, attr_name, self._mask_sensitive_data(attr_value))

        return True

    def _mask_sensitive_data(self, data: str | dict[str, Any]) -> str | dict[str, Any]:
        """Recursively mask sensitive data."""
        if isinstance(data, str):
            for key in self.SENSITIVE_KEYS:
                if key in data.lower():
                    return data.replace(key, f"{key}=***")
            return data
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if key.lower() in self.SENSITIVE_KEYS:
                    masked[key] = "***"
                elif isinstance(value, (str, dict)):
                    masked[key] = self._mask_sensitive_data(value)
                else:
                    masked[key] = value
            return masked
        return data


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add trace ID if available
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id

        # Add performance metrics if available
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms

        # Add error details if exception
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "trace_id",
                "duration_ms",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(self, logger: logging.Logger, operation: str, trace_id: str | None = None):
        self.logger = logger
        self.operation = operation
        self.trace_id = trace_id or str(uuid.uuid4())
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.logger.debug(
            f"Starting {self.operation}",
            extra={"trace_id": self.trace_id, "operation": self.operation},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.perf_counter() - self.start_time) * 1000

            if exc_type is None:
                self.logger.info(
                    f"Completed {self.operation}",
                    extra={
                        "trace_id": self.trace_id,
                        "operation": self.operation,
                        "duration_ms": round(duration_ms, 2),
                    },
                )
            else:
                self.logger.error(
                    f"Failed {self.operation}",
                    extra={
                        "trace_id": self.trace_id,
                        "operation": self.operation,
                        "duration_ms": round(duration_ms, 2),
                        "error_type": exc_type.__name__ if exc_type else None,
                        "error_message": str(exc_val) if exc_val else None,
                    },
                    exc_info=(exc_type, exc_val, exc_tb),
                )


def performance_logged(operation_name: str | None = None):
    """Decorator for automatic performance logging."""

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            logger = logging.getLogger(func.__module__)

            with PerformanceLogger(logger, operation) as perf:
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            logger = logging.getLogger(func.__module__)

            with PerformanceLogger(logger, operation) as perf:
                return func(*args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def setup_logging(
    level: str | None = None, format_type: str = "json", enable_security_filter: bool = True
) -> None:
    """Setup structured logging configuration.

    Args:
    ----
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Logging format ("json" for production, "text" for development)
        enable_security_filter: Whether to enable sensitive data masking

    """
    # Determine log level from environment or parameter
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()

    # Determine format type from environment
    if not level:  # Only use env if not explicitly set
        format_type = os.getenv("LOG_FORMAT", format_type).lower()

    # Configure handlers
    handlers = ["console"]

    # Add file handler if log file specified
    log_file = os.getenv("LOG_FILE")
    if log_file:
        handlers.append("file")

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {},
        "formatters": {},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "level": log_level,
            }
        },
        "root": {
            "level": log_level,
            "handlers": handlers,
        },
        "loggers": {
            "fraiseql_doctor": {
                "level": log_level,
                "handlers": handlers,
                "propagate": False,
            },
        },
    }

    # Add security filter if enabled
    if enable_security_filter:
        config["filters"]["security"] = {
            "()": SecurityFilter,
        }
        config["handlers"]["console"]["filters"] = ["security"]

    # Configure formatter based on type
    if format_type == "json":
        config["formatters"]["structured"] = {
            "()": StructuredFormatter,
        }
        config["handlers"]["console"]["formatter"] = "structured"
    else:
        config["formatters"]["simple"] = {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
        config["handlers"]["console"]["formatter"] = "simple"

    # Add file handler if specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "level": log_level,
            "formatter": "structured" if format_type == "json" else "simple",
        }
        if enable_security_filter:
            config["handlers"]["file"]["filters"] = ["security"]

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration."""
    return logging.getLogger(name)


@contextmanager
def log_context(logger: logging.Logger, **context):
    """Context manager to add contextual information to all log messages."""
    # This is a simplified version - a full implementation would use
    # threading.local or contextvars for proper context isolation
    old_filter = None

    class ContextFilter(logging.Filter):
        def filter(self, record):
            for key, value in context.items():
                setattr(record, key, value)
            return True

    context_filter = ContextFilter()
    logger.addFilter(context_filter)

    try:
        yield
    finally:
        logger.removeFilter(context_filter)


# Initialize logging on import
if not logging.getLogger().handlers:
    setup_logging()

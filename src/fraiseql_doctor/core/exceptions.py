"""Exception classes for FraiseQL Doctor."""


class FraiseQLDoctorError(Exception):
    """Base exception for FraiseQL Doctor."""


class ConfigurationError(FraiseQLDoctorError):
    """Configuration-related errors."""


class DatabaseError(FraiseQLDoctorError):
    """Database-related errors."""


class GraphQLClientError(FraiseQLDoctorError):
    """GraphQL client errors."""

    def __init__(self, message: str, response_time_ms: int = 0):
        super().__init__(message)
        self.response_time_ms = response_time_ms


class GraphQLTimeoutError(GraphQLClientError):
    """GraphQL timeout errors."""

    def __init__(self, message: str, timeout: int, response_time_ms: int = 0):
        super().__init__(message, response_time_ms)
        self.timeout = timeout


class GraphQLAuthError(GraphQLClientError):
    """GraphQL authentication errors."""


class GraphQLComplexityError(GraphQLClientError):
    """GraphQL complexity errors."""


class CircuitBreakerOpenError(GraphQLClientError):
    """Circuit breaker is open."""


class QueryNotFoundError(FraiseQLDoctorError):
    """Query not found."""


class QueryValidationError(FraiseQLDoctorError):
    """Query validation failed."""


class DuplicateQueryError(FraiseQLDoctorError):
    """Duplicate query name."""


class EndpointNotFoundError(FraiseQLDoctorError):
    """Endpoint not found."""


class ExecutionError(FraiseQLDoctorError):
    """Query execution error."""

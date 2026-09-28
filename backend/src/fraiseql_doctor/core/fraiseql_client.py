"""FraiseQL client re-exported for backwards compatibility with tests."""

# Re-export everything from the services module
from ..services.fraiseql_client import (
    AuthenticationError,
    FraiseQLClient,
    GraphQLClientError,
    GraphQLExecutionError,
    GraphQLResponse,
    NetworkError,
)

__all__ = [
    "AuthenticationError",
    "FraiseQLClient",
    "GraphQLClientError",
    "GraphQLExecutionError",
    "GraphQLResponse",
    "NetworkError",
]

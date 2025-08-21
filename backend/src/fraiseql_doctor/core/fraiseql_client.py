"""FraiseQL client re-exported for backwards compatibility with tests."""

# Re-export everything from the services module
from ..services.fraiseql_client import (
    FraiseQLClient,
    GraphQLExecutionError,
    NetworkError,
    AuthenticationError,
    GraphQLClientError,
    GraphQLResponse
)

__all__ = [
    "FraiseQLClient",
    "GraphQLExecutionError", 
    "NetworkError",
    "AuthenticationError",
    "GraphQLClientError",
    "GraphQLResponse"
]
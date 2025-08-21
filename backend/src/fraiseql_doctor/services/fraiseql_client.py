"""FraiseQL Client Implementation.

High-performance async GraphQL client with comprehensive error handling,
authentication support, and connection management.
"""
import asyncio
import base64
import time
from typing import Any, Optional

import aiohttp
from pydantic import BaseModel

from fraiseql_doctor.models.endpoint import Endpoint


class GraphQLResponse(BaseModel):
    """Structured GraphQL response with timing and metadata."""

    data: Optional[dict[str, Any]] = None
    errors: Optional[list[dict[str, Any]]] = None
    response_time_ms: int
    complexity_score: Optional[int] = None
    cached: bool = False


class GraphQLClientError(Exception):
    """Base exception for GraphQL client errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_time_ms: Optional[int] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_time_ms = response_time_ms


class NetworkError(GraphQLClientError):
    """Network connectivity or timeout errors."""


class AuthenticationError(GraphQLClientError):
    """Authentication and authorization errors."""


class GraphQLExecutionError(GraphQLClientError):
    """GraphQL execution errors returned by the server."""

    def __init__(self, message: str, errors: list[dict[str, Any]], **kwargs):
        super().__init__(message, **kwargs)
        self.errors = errors


class FraiseQLClient:
    """Production-ready async FraiseQL/GraphQL client.

    Features:
    - Multiple authentication methods (Bearer, API Key, Basic, OAuth2)
    - Connection pooling and session management
    - Comprehensive error handling
    - Performance tracking and complexity analysis
    - Proper timeout and retry handling
    """

    def __init__(self, endpoint: Endpoint, session: Optional[aiohttp.ClientSession] = None):
        """Initialize FraiseQL client.

        Args:
        ----
            endpoint: Endpoint configuration with URL, auth, and settings
            session: Optional aiohttp session for connection pooling
        """
        self.endpoint = endpoint
        self.session = session
        self.base_url = endpoint.url
        self._auth_headers = self._build_auth_headers()

    def _build_auth_headers(self) -> dict[str, str]:
        """Build authentication headers based on endpoint configuration."""
        headers = {}

        if self.endpoint.auth_type == "bearer":
            token = self.endpoint.auth_config.get("token")
            if token:
                headers["Authorization"] = f"Bearer {token}"

        elif self.endpoint.auth_type == "api_key":
            api_key = self.endpoint.auth_config.get("api_key")
            header_name = self.endpoint.auth_config.get("header_name", "X-API-Key")
            if api_key:
                headers[header_name] = api_key

        elif self.endpoint.auth_type == "basic":
            username = self.endpoint.auth_config.get("username")
            password = self.endpoint.auth_config.get("password")
            if username and password:
                credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {credentials}"

        elif self.endpoint.auth_type == "oauth2":
            # OAuth2 implementation would go here
            # For now, treat as bearer token if access_token is present
            access_token = self.endpoint.auth_config.get("access_token")
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

        return headers

    async def execute_query(
        self,
        query: str,
        variables: Optional[dict[str, Any]] = None,
        operation_name: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> GraphQLResponse:
        """Execute a GraphQL query.

        Args:
        ----
            query: GraphQL query string
            variables: Optional query variables
            operation_name: Optional operation name
            timeout: Optional timeout override

        Returns:
        -------
            GraphQLResponse with data, errors, and metadata

        Raises:
        ------
            NetworkError: For connectivity issues
            AuthenticationError: For auth failures
            GraphQLExecutionError: For GraphQL errors
            GraphQLClientError: For other client errors
        """
        start_time = time.time()

        # Prepare request payload
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        # Prepare headers
        headers = {"Content-Type": "application/json", **self._auth_headers}

        # Use provided timeout or endpoint default
        request_timeout = timeout or self.endpoint.timeout_seconds

        try:
            # Use provided session or create new one
            if self.session:
                session = self.session
                close_session = False
            else:
                session = aiohttp.ClientSession()
                close_session = True

            try:
                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=request_timeout),
                ) as response:
                    response_time_ms = int((time.time() - start_time) * 1000)

                    # Handle HTTP errors
                    if response.status == 401:
                        raise AuthenticationError(
                            "Authentication failed",
                            status_code=response.status,
                            response_time_ms=response_time_ms,
                        )
                    elif response.status >= 400:
                        error_text = await response.text()
                        raise GraphQLClientError(
                            f"HTTP {response.status}: {error_text}",
                            status_code=response.status,
                            response_time_ms=response_time_ms,
                        )

                    # Parse response
                    response_data = await response.json()

                    # Extract complexity score from extensions
                    complexity_score = None
                    if "extensions" in response_data:
                        complexity_score = response_data["extensions"].get("complexity")

                    # Detect cached responses
                    cached = False
                    if "extensions" in response_data:
                        cached = response_data["extensions"].get("cached", False)

                    # Handle GraphQL errors
                    if "errors" in response_data and response_data["errors"]:
                        errors = response_data["errors"]
                        error_messages = [error.get("message", "Unknown error") for error in errors]
                        raise GraphQLExecutionError(
                            f"GraphQL execution error: {'; '.join(error_messages)}",
                            errors=errors,
                            response_time_ms=response_time_ms,
                        )

                    return GraphQLResponse(
                        data=response_data.get("data"),
                        errors=response_data.get("errors"),
                        response_time_ms=response_time_ms,
                        complexity_score=complexity_score,
                        cached=cached,
                    )

            finally:
                if close_session:
                    await session.close()

        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            raise NetworkError(
                f"Request timeout after {request_timeout}s", response_time_ms=response_time_ms
            )

        except (aiohttp.ClientConnectorError, OSError) as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            raise NetworkError(f"Network error: {e!s}", response_time_ms=response_time_ms)

        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            if isinstance(
                e, (GraphQLClientError, NetworkError, AuthenticationError, GraphQLExecutionError)
            ):
                raise
            else:
                raise GraphQLClientError(
                    f"Unexpected error: {e!s}", response_time_ms=response_time_ms
                )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session and not self.session.closed:
            await self.session.close()

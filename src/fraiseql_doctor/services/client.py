"""FraiseQL GraphQL client implementation."""
import asyncio
import json
import time
from typing import Any, Dict, Optional
from uuid import UUID

import aiohttp
from pydantic import BaseModel

from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.core.exceptions import (
    GraphQLClientError,
    GraphQLTimeoutError,
    GraphQLAuthError,
    GraphQLComplexityError
)


class GraphQLResponse(BaseModel):
    """Structured GraphQL response model."""
    data: Dict[str, Any] | None = None
    errors: list[Dict[str, Any]] | None = None
    extensions: Dict[str, Any] | None = None
    response_time_ms: int
    complexity_score: int | None = None
    cached: bool = False


class FraiseQLClient:
    """Production-ready FraiseQL/GraphQL client."""
    
    def __init__(
        self,
        endpoint: Endpoint,
        session: aiohttp.ClientSession | None = None,
        default_timeout: int = 30
    ):
        self.endpoint = endpoint
        self.session = session or aiohttp.ClientSession()
        self.default_timeout = default_timeout
        self._auth_headers: Dict[str, str] = {}
        self._setup_authentication()
    
    def _setup_authentication(self) -> None:
        """Setup authentication headers based on endpoint configuration."""
        if not self.endpoint.auth_type or self.endpoint.auth_type == "none":
            return
        
        auth_config = self.endpoint.auth_config or {}
        
        match self.endpoint.auth_type:
            case "bearer":
                token = auth_config.get("token")
                if token:
                    self._auth_headers["Authorization"] = f"Bearer {token}"
            case "api_key":
                api_key = auth_config.get("api_key")
                header_name = auth_config.get("header_name", "X-API-Key")
                if api_key:
                    self._auth_headers[header_name] = api_key
            case "basic":
                username = auth_config.get("username")
                password = auth_config.get("password")
                if username and password:
                    import base64
                    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                    self._auth_headers["Authorization"] = f"Basic {credentials}"
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers including auth and endpoint headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FraiseQL-Doctor/1.0"
        }
        
        # Add endpoint-specific headers
        if self.endpoint.headers:
            headers.update(self.endpoint.headers)
        
        # Add authentication headers
        headers.update(self._auth_headers)
        
        return headers
    
    def _extract_complexity(self, result: Dict[str, Any]) -> int | None:
        """Extract complexity score from GraphQL extensions."""
        extensions = result.get("extensions", {})
        return extensions.get("complexity") or extensions.get("cost")
    
    def _is_cached_response(self, result: Dict[str, Any]) -> bool:
        """Check if response was served from cache."""
        extensions = result.get("extensions", {})
        return extensions.get("cached", False) or extensions.get("fromCache", False)
    
    async def _handle_http_error(self, response: aiohttp.ClientResponse, response_time_ms: int) -> None:
        """Handle HTTP error responses."""
        content = await response.text()
        
        match response.status:
            case 401 | 403:
                raise GraphQLAuthError(
                    f"Authentication failed: {response.status} - {content}",
                    response_time_ms=response_time_ms
                )
            case 413:
                raise GraphQLComplexityError(
                    f"Query too complex: {content}",
                    response_time_ms=response_time_ms
                )
            case _:
                raise GraphQLClientError(
                    f"HTTP {response.status}: {content}",
                    response_time_ms=response_time_ms
                )
    
    async def execute_query(
        self,
        query: str,
        variables: Dict[str, Any] | None = None,
        operation_name: str | None = None,
        timeout: int | None = None
    ) -> GraphQLResponse:
        """Execute a GraphQL query with comprehensive error handling."""
        start_time = time.time()
        
        try:
            payload = {
                "query": query,
                "variables": variables or {},
            }
            if operation_name:
                payload["operationName"] = operation_name
            
            headers = self._build_headers()
            timeout_val = timeout or self.endpoint.timeout_seconds or self.default_timeout
            
            async with self.session.post(
                str(self.endpoint.url),
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout_val)
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status >= 400:
                    await self._handle_http_error(response, response_time_ms)
                
                result = await response.json()
                
                return GraphQLResponse(
                    data=result.get("data"),
                    errors=result.get("errors"),
                    extensions=result.get("extensions"),
                    response_time_ms=response_time_ms,
                    complexity_score=self._extract_complexity(result),
                    cached=self._is_cached_response(result)
                )
                
        except asyncio.TimeoutError:
            response_time_ms = max(1, int((time.time() - start_time) * 1000))  # Ensure at least 1ms
            raise GraphQLTimeoutError(
                f"Query timeout after {response_time_ms}ms",
                timeout=timeout_val,
                response_time_ms=response_time_ms
            )
        except aiohttp.ClientError as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            raise GraphQLClientError(
                f"Client error: {e}",
                response_time_ms=response_time_ms
            ) from e
    
    async def introspect_schema(self) -> Dict[str, Any]:
        """Perform GraphQL introspection to get schema."""
        introspection_query = """
            query IntrospectionQuery {
                __schema {
                    queryType { name }
                    mutationType { name }
                    subscriptionType { name }
                    types {
                        ...FullType
                    }
                    directives {
                        name
                        description
                        locations
                        args {
                            ...InputValue
                        }
                    }
                }
            }
            
            fragment FullType on __Type {
                kind
                name
                description
                fields(includeDeprecated: true) {
                    name
                    description
                    args {
                        ...InputValue
                    }
                    type {
                        ...TypeRef
                    }
                    isDeprecated
                    deprecationReason
                }
                inputFields {
                    ...InputValue
                }
                interfaces {
                    ...TypeRef
                }
                enumValues(includeDeprecated: true) {
                    name
                    description
                    isDeprecated
                    deprecationReason
                }
                possibleTypes {
                    ...TypeRef
                }
            }
            
            fragment InputValue on __InputValue {
                name
                description
                type { ...TypeRef }
                defaultValue
            }
            
            fragment TypeRef on __Type {
                kind
                name
                ofType {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                }
            }
        """
        
        response = await self.execute_query(introspection_query)
        
        if response.errors:
            raise GraphQLClientError(f"Schema introspection failed: {response.errors}")
        
        return response.data or {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a simple health check query."""
        health_query = "query { __typename }"
        
        try:
            response = await self.execute_query(health_query)
            return {
                "healthy": response.data is not None and not response.errors,
                "response_time_ms": response.response_time_ms,
                "errors": response.errors,
                "cached": response.cached
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "response_time_ms": getattr(e, 'response_time_ms', 0)
            }
    
    async def close(self) -> None:
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()
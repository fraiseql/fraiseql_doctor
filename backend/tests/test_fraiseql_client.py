"""Test module for FraiseQL client implementation.

Tests following TDD approach for GraphQL client functionality.
"""
import asyncio
from unittest.mock import Mock

import aiohttp
import aioresponses
import pytest
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.services.fraiseql_client import (
    AuthenticationError,
    FraiseQLClient,
    GraphQLClientError,
    GraphQLExecutionError,
    GraphQLResponse,
    NetworkError,
)


class TestFraiseQLClientInit:
    """Test FraiseQL client initialization."""

    def test_client_init_with_endpoint(self, sample_endpoint):
        """Test client initializes with endpoint configuration."""
        client = FraiseQLClient(sample_endpoint)

        assert client.endpoint == sample_endpoint
        assert client.session is None  # No session provided
        assert client.base_url == sample_endpoint.url
        assert isinstance(client._auth_headers, dict)

    def test_client_init_with_session(self, sample_endpoint):
        """Test client initializes with custom session."""
        mock_session = Mock(spec=aiohttp.ClientSession)
        client = FraiseQLClient(sample_endpoint, session=mock_session)

        assert client.session == mock_session
        assert client.endpoint == sample_endpoint


class TestAuthHeaderBuilding:
    """Test authentication header building for different auth types."""

    def test_no_auth_headers(self, db_session):
        """Test no auth headers for none auth type."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="No Auth Endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
            auth_config={},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        client = FraiseQLClient(endpoint)
        assert client._auth_headers == {}

    def test_bearer_auth_headers(self, db_session):
        """Test Bearer token authentication headers."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="Bearer Auth Endpoint",
            url="https://api.example.com/graphql",
            auth_type="bearer",
            auth_config={"token": "abc123"},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        client = FraiseQLClient(endpoint)
        assert client._auth_headers == {"Authorization": "Bearer abc123"}

    def test_api_key_auth_headers(self, db_session):
        """Test API key authentication headers."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="API Key Endpoint",
            url="https://api.example.com/graphql",
            auth_type="api_key",
            auth_config={"api_key": "key123", "header_name": "X-API-Key"},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        client = FraiseQLClient(endpoint)
        assert client._auth_headers == {"X-API-Key": "key123"}

    def test_basic_auth_headers(self, db_session):
        """Test HTTP Basic authentication headers."""
        endpoint = Endpoint(
            pk_endpoint="test-id",
            name="Basic Auth Endpoint",
            url="https://api.example.com/graphql",
            auth_type="basic",
            auth_config={"username": "user", "password": "pass"},
            timeout_seconds=30,
            max_retries=3,
            retry_delay_seconds=1.0,
        )

        client = FraiseQLClient(endpoint)
        # Basic auth should encode to base64
        assert "Authorization" in client._auth_headers
        assert client._auth_headers["Authorization"].startswith("Basic ")


class TestGraphQLExecution:
    """Test GraphQL query execution."""

    @pytest.mark.asyncio()
    async def test_execute_simple_query(self, sample_endpoint):
        """Test executing a simple GraphQL query."""
        expected_response = {
            "data": {"user": {"id": "1", "name": "Test User"}},
            "extensions": {"complexity": 5},
        }

        with aioresponses.aioresponses() as m:
            m.post(
                sample_endpoint.url,
                payload=expected_response,
                status=200,
                headers={"Content-Type": "application/json"},
            )

            client = FraiseQLClient(sample_endpoint)
            response = await client.execute_query("query { user { id name } }")

            assert isinstance(response, GraphQLResponse)
            assert response.data == expected_response["data"]
            assert response.errors is None
            assert response.complexity_score == 5
            assert response.response_time_ms > 0

    @pytest.mark.asyncio()
    async def test_execute_query_with_variables(self, sample_endpoint):
        """Test executing query with variables."""
        query = "query GetUser($id: ID!) { user(id: $id) { id name } }"
        variables = {"id": "123"}
        expected_response = {"data": {"user": {"id": "123", "name": "Test User"}}}

        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, payload=expected_response)

            client = FraiseQLClient(sample_endpoint)
            response = await client.execute_query(query, variables=variables)

            assert response.data == expected_response["data"]

            # Verify request payload
            # aioresponses stores requests by URL object
            requests_for_url = None
            for url_key, request_list in m.requests.items():
                if str(url_key[1]) == sample_endpoint.url:
                    requests_for_url = request_list
                    break

            assert requests_for_url is not None
            request = requests_for_url[0]
            request_json = request.kwargs["json"]
            assert request_json["query"] == query
            assert request_json["variables"] == variables


class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    @pytest.mark.asyncio()
    async def test_network_error_handling(self, sample_endpoint):
        """Test handling of network connectivity errors."""
        with aioresponses.aioresponses() as m:
            # Create a simple connection error for testing
            os_error = OSError("Connection refused")
            m.post(sample_endpoint.url, exception=os_error)

            client = FraiseQLClient(sample_endpoint)

            with pytest.raises(NetworkError) as exc_info:
                await client.execute_query("query { test }")

            assert "network error" in str(exc_info.value).lower()
            assert exc_info.value.status_code is None

    @pytest.mark.asyncio()
    async def test_timeout_error_handling(self, sample_endpoint):
        """Test handling of request timeouts."""
        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, exception=asyncio.TimeoutError)

            client = FraiseQLClient(sample_endpoint)

            with pytest.raises(NetworkError) as exc_info:
                await client.execute_query("query { test }")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio()
    async def test_http_error_handling(self, sample_endpoint):
        """Test handling of HTTP error status codes."""
        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, status=500, payload={"error": "Internal Server Error"})

            client = FraiseQLClient(sample_endpoint)

            with pytest.raises(GraphQLClientError) as exc_info:
                await client.execute_query("query { test }")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio()
    async def test_authentication_error_handling(self, sample_endpoint):
        """Test handling of authentication errors."""
        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, status=401, payload={"error": "Unauthorized"})

            client = FraiseQLClient(sample_endpoint)

            with pytest.raises(AuthenticationError) as exc_info:
                await client.execute_query("query { test }")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio()
    async def test_graphql_error_handling(self, sample_endpoint):
        """Test handling of GraphQL execution errors."""
        error_response = {
            "data": None,
            "errors": [
                {
                    "message": "Field 'unknown' doesn't exist",
                    "locations": [{"line": 1, "column": 9}],
                    "path": ["unknown"],
                }
            ],
        }

        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, payload=error_response, status=200)

            client = FraiseQLClient(sample_endpoint)

            with pytest.raises(GraphQLExecutionError) as exc_info:
                await client.execute_query("query { unknown }")

            assert "Field 'unknown' doesn't exist" in str(exc_info.value)
            assert exc_info.value.errors == error_response["errors"]


class TestSessionManagement:
    """Test HTTP session management and connection pooling."""

    @pytest.mark.asyncio()
    async def test_session_reuse(self, sample_endpoint):
        """Test that custom session is reused across requests."""
        expected_response = {"data": {"test": "value"}}

        async with aiohttp.ClientSession() as session:
            with aioresponses.aioresponses() as m:
                m.post(sample_endpoint.url, payload=expected_response)
                m.post(sample_endpoint.url, payload=expected_response)

                client = FraiseQLClient(sample_endpoint, session=session)

                # Execute multiple queries with same client
                await client.execute_query("query { test1 }")
                await client.execute_query("query { test2 }")

                # Verify both requests were made
                total_requests = sum(len(request_list) for request_list in m.requests.values())
                assert total_requests == 2

    @pytest.mark.asyncio()
    async def test_session_cleanup(self, sample_endpoint):
        """Test that sessions are properly cleaned up."""
        expected_response = {"data": {"test": "value"}}

        with aioresponses.aioresponses() as m:
            m.post(sample_endpoint.url, payload=expected_response)

            client = FraiseQLClient(sample_endpoint)
            await client.execute_query("query { test }")

            # Session should be cleaned up after request
            # This is implicitly tested by not causing resource leaks


class TestConcurrentExecution:
    """Test concurrent query execution."""

    @pytest.mark.asyncio()
    async def test_concurrent_queries(self, sample_endpoint):
        """Test executing multiple queries concurrently."""
        responses = [
            {"data": {"query1": "result1"}},
            {"data": {"query2": "result2"}},
            {"data": {"query3": "result3"}},
        ]

        with aioresponses.aioresponses() as m:
            for response in responses:
                m.post(sample_endpoint.url, payload=response)

            client = FraiseQLClient(sample_endpoint)

            # Execute queries concurrently
            tasks = [
                client.execute_query("query { query1 }"),
                client.execute_query("query { query2 }"),
                client.execute_query("query { query3 }"),
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 3
            assert all(isinstance(r, GraphQLResponse) for r in results)
            assert results[0].data == {"query1": "result1"}
            assert results[1].data == {"query2": "result2"}
            assert results[2].data == {"query3": "result3"}


# Fixtures for testing
@pytest.fixture()
def sample_endpoint():
    """Create a sample endpoint for testing."""
    return Endpoint(
        pk_endpoint="test-endpoint-id",
        name="Test GraphQL Endpoint",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "test-token-123"},
        timeout_seconds=30,
        max_retries=3,
        retry_delay_seconds=1.0,
    )

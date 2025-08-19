"""Test comprehensive data validation rules."""
import pytest
from pydantic import ValidationError
from fraiseql_doctor.schemas.query import QueryCreate
from fraiseql_doctor.schemas.endpoint import EndpointCreate


def test_query_creation_validation():
    """Test query creation validation rules."""
    # Valid query should pass
    valid_query = QueryCreate(
        name="valid-query",
        query_text="query { user { id name } }",
        variables={"limit": 10},
        tags=["test", "user"],
        created_by="test-user"
    )
    assert valid_query.name == "valid-query"
    
    # Invalid query should fail validation
    with pytest.raises(ValidationError):
        QueryCreate(
            name="",  # Empty name should fail
            query_text="query { user { id name } }",
            created_by="test-user"
        )
    
    with pytest.raises(ValidationError):
        QueryCreate(
            name="valid-name",
            query_text="",  # Empty query should fail
            created_by="test-user"
        )


def test_endpoint_creation_validation():
    """Test endpoint creation validation rules."""
    # Valid endpoint should pass
    valid_endpoint = EndpointCreate(
        name="test-api",
        url="https://api.example.com/graphql",
        auth_type="bearer",
        auth_config={"token": "secret"},
        timeout_seconds=30
    )
    assert valid_endpoint.name == "test-api"
    
    # Invalid URL should fail
    with pytest.raises(ValidationError):
        EndpointCreate(
            name="test-api",
            url="not-a-url",  # Invalid URL
            auth_type="none"
        )
    
    # Invalid auth type should fail
    with pytest.raises(ValidationError):
        EndpointCreate(
            name="test-api", 
            url="https://api.example.com/graphql",
            auth_type="invalid-auth-type"  # Not in allowed list
        )


def test_query_name_validation():
    """Test query name validation edge cases."""
    # Whitespace should be stripped
    query = QueryCreate(
        name="  valid-name  ",
        query_text="query { test }",
        created_by="test"
    )
    assert query.name == "valid-name"
    
    # Empty after strip should fail
    with pytest.raises(ValidationError):
        QueryCreate(
            name="   ",  # Only whitespace
            query_text="query { test }",
            created_by="test"
        )


def test_query_text_validation():
    """Test GraphQL query text validation."""
    # Valid query operations should pass
    valid_queries = [
        "query { user { id } }",
        "mutation { createUser(input: {name: \"test\"}) { id } }",
        "QUERY GetUsers { users { id name } }",  # Case insensitive
    ]
    
    for query_text in valid_queries:
        query = QueryCreate(
            name="test-query",
            query_text=query_text,
            created_by="test"
        )
        assert query.query_text == query_text.strip()
    
    # Invalid query text should fail
    with pytest.raises(ValidationError):
        QueryCreate(
            name="test-query",
            query_text="{ user { id } }",  # Missing query/mutation keyword
            created_by="test"
        )


def test_endpoint_url_validation():
    """Test endpoint URL validation edge cases."""
    # Valid URLs should pass
    valid_urls = [
        "https://api.example.com/graphql",
        "http://localhost:4000/graphql",
        "https://subdomain.example.com:8080/path/graphql",
    ]
    
    for url in valid_urls:
        endpoint = EndpointCreate(
            name="test-endpoint",
            url=url,
            auth_type="none"
        )
        assert endpoint.url == url
    
    # Invalid URLs should fail
    invalid_urls = [
        "ftp://example.com/graphql",  # Wrong protocol
        "api.example.com/graphql",   # Missing protocol
        "",                          # Empty
        "   ",                       # Only whitespace
    ]
    
    for url in invalid_urls:
        with pytest.raises(ValidationError):
            EndpointCreate(
                name="test-endpoint",
                url=url,
                auth_type="none"
            )


def test_endpoint_auth_type_validation():
    """Test authentication type validation."""
    # Valid auth types should pass
    valid_auth_types = ["none", "bearer", "basic", "api_key", "oauth2"]
    
    for auth_type in valid_auth_types:
        endpoint = EndpointCreate(
            name="test-endpoint",
            url="https://api.example.com/graphql",
            auth_type=auth_type
        )
        assert endpoint.auth_type == auth_type
    
    # Invalid auth types should fail
    invalid_auth_types = ["invalid", "jwt", "custom", ""]
    
    for auth_type in invalid_auth_types:
        with pytest.raises(ValidationError):
            EndpointCreate(
                name="test-endpoint",
                url="https://api.example.com/graphql",
                auth_type=auth_type
            )


def test_query_tags_validation():
    """Test query tags validation and cleaning."""
    # Tags should be cleaned of empty strings and whitespace
    query = QueryCreate(
        name="test-query",
        query_text="query { test }",
        tags=["valid", "  another  ", "", "  ", "third"],
        created_by="test"
    )
    
    # Should remove empty and whitespace-only tags, and strip whitespace
    expected_tags = ["valid", "another", "third"]
    assert query.tags == expected_tags


def test_endpoint_timeout_validation():
    """Test endpoint timeout validation."""
    # Valid timeouts should pass
    endpoint = EndpointCreate(
        name="test-endpoint",
        url="https://api.example.com/graphql",
        auth_type="none",
        timeout_seconds=60
    )
    assert endpoint.timeout_seconds == 60
    
    # Invalid timeouts should fail
    with pytest.raises(ValidationError):
        EndpointCreate(
            name="test-endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
            timeout_seconds=0  # Too low
        )
    
    with pytest.raises(ValidationError):
        EndpointCreate(
            name="test-endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
            timeout_seconds=400  # Too high
        )
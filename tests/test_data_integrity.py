"""Test database data integrity and constraints."""
import pytest
from sqlalchemy import select
from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.endpoint import Endpoint


async def test_query_name_uniqueness(db_session):
    """Test that query names must be unique."""
    # Create first query
    query1 = Query(
        name="test-query",
        query_text="query { user { id } }",
        created_by="test"
    )
    db_session.add(query1)
    await db_session.commit()
    
    # Attempt to create duplicate name should fail
    query2 = Query(
        name="test-query",  # Same name
        query_text="query { product { id } }",
        created_by="test"
    )
    db_session.add(query2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.commit()


async def test_endpoint_url_validation(db_session):
    """Test that endpoint URLs are validated."""
    # Valid URL should work
    endpoint = Endpoint(
        name="test-endpoint",
        url="https://api.example.com/graphql",
        auth_type="none"
    )
    db_session.add(endpoint)
    await db_session.commit()
    
    # Verify it was saved
    result = await db_session.execute(
        select(Endpoint).where(Endpoint.name == "test-endpoint")
    )
    saved_endpoint = result.scalar_one()
    assert saved_endpoint.url == "https://api.example.com/graphql"


async def test_query_variables_jsonb_storage(db_session):
    """Test that query variables are properly stored as JSONB."""
    complex_variables = {
        "filters": {
            "status": ["active", "pending"],
            "createdAfter": "2024-01-01T00:00:00Z"
        },
        "pagination": {"limit": 50, "offset": 0},
        "includeDeleted": False
    }
    
    query = Query(
        name="complex-query",
        query_text="query($filters: FilterInput!) { items(filters: $filters) { id } }",
        variables=complex_variables,
        created_by="test"
    )
    db_session.add(query)
    await db_session.commit()
    
    # Reload and verify JSONB integrity
    result = await db_session.execute(
        select(Query).where(Query.name == "complex-query")
    )
    saved_query = result.scalar_one()
    assert saved_query.variables == complex_variables
    assert isinstance(saved_query.variables["filters"]["status"], list)


async def test_endpoint_name_uniqueness(db_session):
    """Test that endpoint names must be unique."""
    # Create first endpoint
    endpoint1 = Endpoint(
        name="api-endpoint",
        url="https://api1.example.com/graphql",
        auth_type="none"
    )
    db_session.add(endpoint1)
    await db_session.commit()
    
    # Attempt to create duplicate name should fail
    endpoint2 = Endpoint(
        name="api-endpoint",  # Same name
        url="https://api2.example.com/graphql",
        auth_type="none"
    )
    db_session.add(endpoint2)
    
    with pytest.raises(Exception):  # Should raise integrity error
        await db_session.commit()
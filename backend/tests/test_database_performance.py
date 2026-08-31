"""Test database performance requirements."""

import time

import pytest
from sqlalchemy import select

from fraiseql_doctor.models.query import Query


@pytest.mark.performance
async def test_query_list_performance(db_session):
    """Test that listing queries meets performance requirements."""
    # Create test data
    queries = []
    for i in range(100):
        query = Query(
            name=f"perf-test-{i}",
            query_text=f'query Test{i} {{ user(id: "{i}") {{ id name }} }}',
            tags=[f"tag-{i % 5}"],  # Some overlapping tags
            created_by="perf-test",
        )
        queries.append(query)

    db_session.add_all(queries)
    await db_session.commit()

    # Test query performance
    start_time = time.time()
    result = await db_session.execute(
        select(Query)
        .where(Query.created_by == "perf-test")
        .order_by(Query.created_at.desc())
        .limit(20)
    )
    queries_result = result.scalars().all()
    query_time = time.time() - start_time

    assert len(queries_result) == 20
    assert query_time < 0.1  # Should complete in < 100ms


@pytest.mark.performance
async def test_execution_history_query_performance(db_session):
    """Test execution history queries meet performance requirements."""
    # This test defines the performance requirement
    # Implementation will need proper indexing to pass

    # Setup will be implemented after models exist


async def test_jsonb_query_performance(db_session):
    """Test JSONB queries are properly indexed and performant."""
    # Create queries with searchable tags
    queries = []
    for i in range(50):
        query = Query(
            name=f"jsonb-test-{i}",
            query_text="query { test }",
            tags=["performance", f"category-{i % 3}"],
            query_metadata={"complexity": i % 10, "category": f"cat-{i % 3}"},
            created_by="jsonb-test",
        )
        queries.append(query)

    db_session.add_all(queries)
    await db_session.commit()

    # Test tag-based search performance
    start_time = time.time()
    result = await db_session.execute(select(Query).where(Query.tags.contains(["performance"])))
    tagged_queries = result.scalars().all()
    search_time = time.time() - start_time

    assert len(tagged_queries) == 50
    assert search_time < 0.05  # Should be very fast with GIN index

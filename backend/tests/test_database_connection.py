"""Test database connectivity and basic operations."""

from sqlalchemy import text
from fraiseql_doctor.core.database import get_database_session


async def test_database_connection(test_engine):
    """Test that database connection works."""
    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 as test_value"))
        row = result.fetchone()
        assert row[0] == 1


async def test_database_session_creation(db_session):
    """Test that database sessions can be created."""
    assert db_session is not None
    # Session should support basic operations
    result = await db_session.execute(text("SELECT 1 as test_value"))
    row = result.fetchone()
    assert row[0] == 1

"""Database fixtures for testing with real PostgreSQL."""
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database configuration
TEMPLATE_DB_NAME = "fraiseql_doctor_db_test_template"
TEST_DB_NAME = "fraiseql_doctor_db_test"
# Use current user for database connection
current_user = os.getenv("USER", "postgres")
TEST_DATABASE_URL = f"postgresql+asyncpg://{current_user}@localhost/{TEST_DB_NAME}"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine with proper setup/teardown."""
    # Create test database from template (very fast)
    await _recreate_test_database_from_template()

    # Create async engine for the test database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=2,
        max_overflow=0,
        pool_recycle=300,
    )

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic rollback."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def fresh_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh database session that commits changes.

    Use this fixture when you need to test actual database persistence
    or when testing across multiple sessions.
    """
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # This fixture allows commits, so cleanup is manual if needed


async def _recreate_test_database_from_template():
    """Recreate test database from template (fast operation)."""
    # Use synchronous connection for database operations
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    # Connect to postgres database to manage other databases
    conn = psycopg2.connect(
        host="localhost", database="postgres", user=os.getenv("USER", "postgres")
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Drop test database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")

        # Create test database from template (this is very fast)
        cursor.execute(f"CREATE DATABASE {TEST_DB_NAME} TEMPLATE {TEMPLATE_DB_NAME}")

    finally:
        cursor.close()
        conn.close()


@pytest.fixture(scope="session")
def setup_test_database():
    """Ensure template database exists and is up to date.

    This fixture runs once per test session to ensure the template
    database is properly set up with migrations.
    """
    import subprocess

    # Check if template database exists, create if not
    try:
        result = subprocess.run(
            ["psql", "-lqt", "-h", "localhost"], capture_output=True, text=True, check=True
        )

        if TEMPLATE_DB_NAME not in result.stdout:
            # Create template database
            subprocess.run(["createdb", TEMPLATE_DB_NAME], check=True)

            # Run migrations on template
            subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=True)

    except subprocess.CalledProcessError as e:
        pytest.skip(f"Could not set up test database: {e}")

    return True


# Convenience fixtures for different test scenarios
@pytest_asyncio.fixture
async def empty_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an empty database session for testing migrations or schema."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Truncate all tables to start fresh
        async with session.begin():
            # Get all table names
            result = await session.execute(
                text(
                    """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public' AND tablename LIKE 'tb_%'
            """
                )
            )
            tables = [row[0] for row in result]

            # Truncate all tables
            if tables:
                table_list = ", ".join(tables)
                await session.execute(text(f"TRUNCATE {table_list} CASCADE"))

        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def seeded_db_session(db_session) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session with basic test data."""
    from fraiseql_doctor.models.endpoint import Endpoint
    from fraiseql_doctor.models.query import Query

    # Add some basic test data
    test_query = Query(
        name="test-query",
        query_text="query { user { id name } }",
        created_by="test-user",
        tags=["test", "basic"],
    )

    test_endpoint = Endpoint(
        name="test-endpoint", url="https://api.test.com/graphql", auth_type="none"
    )

    db_session.add(test_query)
    db_session.add(test_endpoint)
    await db_session.flush()  # Get IDs without committing

    yield db_session


# Performance testing fixture
@pytest_asyncio.fixture
async def performance_db_session(fresh_db_session) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session optimized for performance testing.

    This fixture commits data and can be used for realistic performance tests.
    """
    yield fresh_db_session

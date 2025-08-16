"""Database test fixtures following TDD methodology."""

import asyncio
import os
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session

from fraiseql_doctor.core.config import DatabaseConfig, Settings
from fraiseql_doctor.core.database import DatabaseManager
from fraiseql_doctor.models import Base


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Create a test database URL with random name to avoid conflicts."""
    # Use a temporary database name to avoid conflicts
    db_name = f"fraiseql_doctor_test_{uuid4().hex[:8]}"
    
    # Use environment variable if set, otherwise default to localhost
    postgres_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres@localhost:5432")
    base_url = postgres_url.rstrip("/")
    
    return f"{base_url}/{db_name}"


@pytest.fixture(scope="session")
def test_settings(test_database_url: str) -> Settings:
    """Create test settings with isolated test database."""
    return Settings(
        database=DatabaseConfig(
            url=test_database_url,
            pool_size=5,
            max_overflow=10,
            echo=False,  # Set to True for SQL debugging
        ),
    )


@pytest.fixture(scope="session")
def test_database_manager(test_settings: Settings) -> DatabaseManager:
    """Create database manager for testing."""
    # Clear any existing global database manager to avoid conflicts
    from fraiseql_doctor.core.database import _db_manager
    import fraiseql_doctor.core.database as db_module
    
    # Store original global state
    original_manager = db_module._db_manager
    
    # Create test manager
    test_manager = DatabaseManager(test_settings)
    
    # Set as global manager for tests that might use the global functions
    db_module._db_manager = test_manager
    
    try:
        yield test_manager
    finally:
        # Restore original global state
        db_module._db_manager = original_manager


@pytest_asyncio.fixture(scope="session")
async def test_database(test_database_url: str, test_database_manager: DatabaseManager):
    """Setup isolated test database with migrations.
    
    This follows TDD RED->GREEN->REFACTOR:
    RED: Tests expect clean database with tables
    GREEN: Create database and run migrations
    REFACTOR: Optimize with template pattern for speed
    """
    # Extract database name from URL
    db_name = test_database_url.split("/")[-1]
    base_url = "/".join(test_database_url.split("/")[:-1])
    
    # Create database
    admin_engine = create_engine(f"{base_url}/postgres")
    
    # Create database (must be done outside a transaction)
    with admin_engine.connect() as conn:
        conn.execute(text("COMMIT"))  # End any existing transaction
        conn.execute(text(f"CREATE DATABASE {db_name}"))
        conn.commit()
    
    try:
        # GREEN PHASE: Create tables directly (minimal implementation to make test pass)
        # Later we can refactor to use Alembic properly
        await test_database_manager.create_tables_async()
        
        yield test_database_manager
        
    finally:
        # Cleanup: Drop the test database
        admin_engine = create_engine(f"{base_url}/postgres")
        with admin_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            # Terminate connections to the test database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = '{db_name}' AND pid <> pg_backend_pid()
            """))
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            conn.commit()


async def _run_migrations_async(database_url: str) -> None:
    """Run Alembic migrations asynchronously using existing alembic.ini."""
    def run_migrations():
        # Ensure we're in the project root directory
        import os
        from pathlib import Path
        
        # Find the project root (where alembic.ini would be)
        current_dir = Path.cwd()
        project_root = current_dir
        while not (project_root / "alembic.ini").exists() and project_root.parent != project_root:
            project_root = project_root.parent
        
        # Change to project root for migration
        old_cwd = os.getcwd()
        os.chdir(project_root)
        
        try:
            # Use existing alembic.ini and override the database URL
            config = Config("alembic.ini")
            config.set_main_option("sqlalchemy.url", database_url)
            
            print(f"Running migrations on: {database_url}")
            print(f"Using config from: {project_root / 'alembic.ini'}")
            
            # Run the upgrade
            print("Running alembic upgrade head...")
            command.upgrade(config, "head")
            print("Alembic upgrade completed")
            
            # Verify migration worked
            from sqlalchemy import create_engine, text
            engine = create_engine(database_url)
            with engine.connect() as conn:
                try:
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    current_db_rev = result.fetchone()
                    print(f"Migration successful! Database version: {current_db_rev[0] if current_db_rev else 'None'}")
                except Exception as e:
                    print(f"Migration verification failed: {e}")
                        
        finally:
            # Restore original working directory
            os.chdir(old_cwd)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_migrations)


@pytest_asyncio.fixture
async def db_session(test_database: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """Provide transactional database session with automatic rollback.
    
    TDD Implementation:
    RED: Test expects rollback after each test
    GREEN: Implement session with rollback
    REFACTOR: Add connection pooling optimization
    """
    async with test_database.get_async_session() as session:
        # Start a nested transaction
        trans = await session.begin()
        try:
            yield session
        finally:
            # Always rollback to ensure test isolation
            await trans.rollback()


@pytest.fixture
def sync_db_session(test_database: DatabaseManager) -> Generator[Session, None, None]:
    """Provide synchronous transactional database session."""
    with test_database.get_session() as session:
        # Start a nested transaction
        trans = session.begin()
        try:
            yield session
        finally:
            # Always rollback to ensure test isolation
            trans.rollback()


@pytest_asyncio.fixture
async def clean_database(test_database: DatabaseManager) -> AsyncGenerator[DatabaseManager, None]:
    """Provide a completely clean database for integration tests.
    
    This fixture truncates all tables between tests for scenarios
    that need a pristine database state.
    """
    async with test_database.get_async_session() as session:
        # Get all table names
        result = await session.execute(text("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            AND tablename != 'alembic_version'
        """))
        tables = result.fetchall()
        
        # Truncate all tables (except alembic_version)
        if tables:
            table_names = ", ".join(f'"{table[0]}"' for table in tables)
            await session.execute(text(f"TRUNCATE {table_names} CASCADE"))
            await session.commit()
    
    yield test_database


# Performance testing fixtures
@pytest.fixture
def db_connection_pool(test_database: DatabaseManager):
    """Provide connection pool for performance testing."""
    return test_database.async_engine


@pytest_asyncio.fixture
async def multiple_db_sessions(test_database: DatabaseManager, request):
    """Provide multiple concurrent database sessions for load testing."""
    session_count = getattr(request, 'param', 5)  # Default to 5 sessions
    
    sessions = []
    try:
        for _ in range(session_count):
            session = test_database.async_session_factory()
            sessions.append(session)
        
        yield sessions
        
    finally:
        # Clean up all sessions
        for session in sessions:
            await session.close()


# Utility fixtures for test data
@pytest_asyncio.fixture
async def sample_endpoint_data():
    """Provide sample endpoint data for testing."""
    return {
        "name": "test-api",
        "url": "https://api.example.com/graphql",
        "auth_type": "bearer",
        "auth_config": {"token": "test-token-123"},
        "description": "Test endpoint for integration testing",
        "timeout_seconds": 30,
    }


@pytest_asyncio.fixture
async def sample_query_data():
    """Provide sample query data for testing."""
    return {
        "name": "test-query",
        "query_text": '''
            query GetUsers($limit: Int = 10) {
                users(limit: $limit) {
                    id
                    name
                    email
                    createdAt
                }
            }
        ''',
        "variables": {"limit": 5},
        "description": "Test query for user listing",
    }


# Migration testing utilities
@pytest_asyncio.fixture
async def migration_tester(test_database_url: str):
    """Provide utilities for testing database migrations."""
    
    class MigrationTester:
        def __init__(self, db_url: str):
            self.db_url = db_url
        
        async def downgrade_to(self, revision: str):
            """Downgrade database to specific revision."""
            config = Config("alembic.ini")
            config.set_main_option("sqlalchemy.url", self.db_url)
            
            def downgrade():
                command.downgrade(config, revision)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, downgrade)
        
        async def upgrade_to(self, revision: str):
            """Upgrade database to specific revision."""
            config = Config("alembic.ini")
            config.set_main_option("sqlalchemy.url", self.db_url)
            
            def upgrade():
                command.upgrade(config, revision)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, upgrade)
        
        async def get_current_revision(self) -> str:
            """Get current database revision."""
            engine = create_async_engine(self.db_url)
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT version_num FROM alembic_version"))
                row = result.fetchone()
                return row[0] if row else None
    
    return MigrationTester(test_database_url)
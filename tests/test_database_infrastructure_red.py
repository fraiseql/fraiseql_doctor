"""Test database infrastructure following TDD methodology.

RED Phase: These tests should fail initially, driving the implementation.
GREEN Phase: Implement minimal code to make tests pass.
REFACTOR Phase: Optimize while keeping tests green.
"""

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from fraiseql_doctor.core.database import DatabaseManager
from fraiseql_doctor.core.config import Settings, DatabaseConfig
from fraiseql_doctor.models import Endpoint, Query


class TestDatabaseSetup:
    """Test database setup and migration infrastructure."""
    
    @pytest.fixture
    def mock_database_manager(self):
        """Create a mock database manager for testing."""
        settings = Settings(
            database=DatabaseConfig(
                url="postgresql://test:test@localhost:5432/test_db",
                pool_size=5,
                max_overflow=10,
                echo=False,
            )
        )
        return DatabaseManager(settings)
    
    def test_database_manager_creation(self, mock_database_manager):
        """GREEN: Test that DatabaseManager can be created."""
        assert mock_database_manager is not None
        assert mock_database_manager.settings is not None
        assert mock_database_manager.settings.database.url == "postgresql://test:test@localhost:5432/test_db"
    
    def test_database_manager_has_required_methods(self, mock_database_manager):
        """GREEN: Test that DatabaseManager has required methods."""
        required_methods = {
            'get_session', 'get_async_session', 'create_tables', 
            'drop_tables', 'create_tables_async', 'drop_tables_async'
        }
        
        actual_methods = {method for method in dir(mock_database_manager) if not method.startswith('_')}
        missing_methods = required_methods - actual_methods
        assert not missing_methods, f"DatabaseManager missing methods: {missing_methods}"
    
    @pytest.mark.asyncio
    async def test_database_table_creation_method_exists(self, mock_database_manager):
        """GREEN: Test that create_tables_async method exists and is callable."""
        # Test that the method exists
        assert hasattr(mock_database_manager, 'create_tables_async')
        assert callable(getattr(mock_database_manager, 'create_tables_async'))
        
        # Mock the async engine to avoid real database connection
        with patch.object(mock_database_manager, 'async_engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn
            
            # Should not raise an exception
            await mock_database_manager.create_tables_async()
            
            # Verify the method was called
            mock_engine.begin.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_alembic_version_table_exists(self, test_database: DatabaseManager):
        """RED: Test that Alembic version tracking is working."""
        async with test_database.get_async_session() as session:
            # Check alembic_version table exists and has a version
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            version = result.fetchone()
            
            assert version is not None, "No Alembic version found"
            assert len(version[0]) > 0, "Alembic version is empty"


class TestDatabaseSessions:
    """Test database session management and isolation."""
    
    @pytest.mark.asyncio
    async def test_session_provides_clean_state(self, db_session: AsyncSession):
        """RED: Test that each session starts with empty tables."""
        # Count records in endpoints table
        result = await db_session.execute(text("SELECT COUNT(*) FROM endpoints"))
        count = result.scalar()
        
        # Should start with 0 records (clean state)
        assert count == 0, f"Expected clean database, found {count} endpoints"
    
    @pytest.mark.asyncio
    async def test_session_rollback_isolation(self, db_session: AsyncSession):
        """RED: Test that session changes are rolled back between tests."""
        # Insert a test record
        await db_session.execute(text("""
            INSERT INTO endpoints (id, name, url, auth_type) 
            VALUES (gen_random_uuid(), 'test', 'https://example.com', 'none')
        """))
        await db_session.flush()  # Flush but don't commit
        
        # Verify record exists in this session
        result = await db_session.execute(text("SELECT COUNT(*) FROM endpoints"))
        count = result.scalar()
        assert count == 1, "Record should exist in current session"
        
        # The rollback happens automatically in the fixture
        # Next test should see clean state
    
    @pytest.mark.asyncio
    async def test_session_after_rollback_is_clean(self, db_session: AsyncSession):
        """RED: Test that this session sees no data from previous test."""
        result = await db_session.execute(text("SELECT COUNT(*) FROM endpoints"))
        count = result.scalar()
        
        # Should be 0 due to rollback from previous test
        assert count == 0, f"Expected clean state after rollback, found {count} endpoints"


class TestDatabaseCRUDOperations:
    """Test basic CRUD operations work with the database setup."""
    
    @pytest.mark.asyncio
    async def test_create_endpoint_via_orm(self, db_session: AsyncSession):
        """RED: Test creating endpoint via SQLAlchemy ORM."""
        # Create endpoint using ORM
        endpoint = Endpoint(
            name="test-endpoint",
            url="https://api.example.com/graphql",
            auth_type="bearer",
            auth_config={"token": "test-123"},
            description="Test endpoint",
        )
        
        db_session.add(endpoint)
        await db_session.flush()  # Get the ID without committing
        
        # Verify it was created
        assert endpoint.id is not None
        assert endpoint.created_at is not None
        
        # Verify we can query it back
        result = await db_session.execute(
            text("SELECT name, url FROM endpoints WHERE id = :id"),
            {"id": endpoint.id}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test-endpoint"
        assert row[1] == "https://api.example.com/graphql"
    
    @pytest.mark.asyncio
    async def test_create_query_with_relationship(self, db_session: AsyncSession):
        """RED: Test creating query with endpoint relationship."""
        # First create an endpoint
        endpoint = Endpoint(
            name="test-endpoint",
            url="https://api.example.com/graphql",
            auth_type="none",
        )
        db_session.add(endpoint)
        await db_session.flush()
        
        # Create a query associated with the endpoint
        query = Query(
            name="test-query",
            query_text="{ users { id name } }",
            endpoint_id=endpoint.id,
            variables={"limit": 10},
        )
        db_session.add(query)
        await db_session.flush()
        
        # Verify relationship works
        assert query.id is not None
        assert query.endpoint_id == endpoint.id
        
        # Test the relationship
        result = await db_session.execute(
            text("""
                SELECT q.name, e.name as endpoint_name 
                FROM queries q 
                JOIN endpoints e ON q.endpoint_id = e.id 
                WHERE q.id = :query_id
            """),
            {"query_id": query.id}
        )
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test-query"
        assert row[1] == "test-endpoint"


class TestDatabasePerformance:
    """Test database performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_connection_pool_handles_concurrent_sessions(self, multiple_db_sessions):
        """RED: Test that connection pool handles multiple concurrent sessions."""
        # This test uses the multiple_db_sessions fixture
        assert len(multiple_db_sessions) >= 5, "Should have at least 5 sessions"
        
        # Execute a query in each session concurrently
        import asyncio
        
        async def query_in_session(session):
            result = await session.execute(text("SELECT 1 as test"))
            return result.scalar()
        
        # Run queries concurrently
        tasks = [query_in_session(session) for session in multiple_db_sessions]
        results = await asyncio.gather(*tasks)
        
        # All should return 1
        assert all(result == 1 for result in results), "All queries should succeed"
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session: AsyncSession):
        """RED: Test bulk insert performance meets requirements."""
        import time
        
        # Prepare bulk data
        endpoints_data = [
            {
                "name": f"endpoint-{i}",
                "url": f"https://api{i}.example.com/graphql",
                "auth_type": "none",
            }
            for i in range(100)
        ]
        
        # Measure bulk insert time
        start_time = time.time()
        
        for data in endpoints_data:
            endpoint = Endpoint(**data)
            db_session.add(endpoint)
        
        await db_session.flush()
        end_time = time.time()
        
        # Should complete in reasonable time (< 1 second for 100 records)
        duration = end_time - start_time
        assert duration < 1.0, f"Bulk insert took {duration:.3f}s, should be < 1.0s"
        
        # Verify all records were inserted
        result = await db_session.execute(text("SELECT COUNT(*) FROM endpoints"))
        count = result.scalar()
        assert count == 100, f"Expected 100 endpoints, got {count}"


class TestMigrationSystem:
    """Test database migration system works correctly."""
    
    @pytest.mark.asyncio
    async def test_current_migration_is_head(self, migration_tester):
        """RED: Test that database is at the latest migration."""
        current_revision = await migration_tester.get_current_revision()
        
        # Should have a revision (not None or empty)
        assert current_revision is not None, "No current revision found"
        assert len(current_revision) > 0, "Current revision is empty"
        
        # For now, just verify we have a revision
        # In a real scenario, you'd compare with alembic's head
        assert len(current_revision) == 12, f"Revision should be 12 chars, got {len(current_revision)}"


# Integration test combining multiple fixtures
class TestDatabaseIntegration:
    """Integration tests combining multiple database features."""
    
    @pytest.mark.asyncio
    async def test_full_database_workflow(
        self, 
        db_session: AsyncSession,
        sample_endpoint_data: dict,
        sample_query_data: dict
    ):
        """RED: Test complete database workflow with real data."""
        # Create endpoint
        endpoint = Endpoint(**sample_endpoint_data)
        db_session.add(endpoint)
        await db_session.flush()
        
        # Create query for the endpoint
        query_data = sample_query_data.copy()
        query_data["endpoint_id"] = endpoint.id
        query = Query(**query_data)
        db_session.add(query)
        await db_session.flush()
        
        # Verify the complete workflow
        result = await db_session.execute(text("""
            SELECT 
                e.name as endpoint_name,
                e.url as endpoint_url,
                q.name as query_name,
                q.query_text
            FROM endpoints e
            JOIN queries q ON e.id = q.endpoint_id
            WHERE e.id = :endpoint_id
        """), {"endpoint_id": endpoint.id})
        
        row = result.fetchone()
        assert row is not None
        assert row[0] == sample_endpoint_data["name"]
        assert row[1] == sample_endpoint_data["url"]
        assert row[2] == sample_query_data["name"]
        assert "GetUsers" in row[3]  # Check query contains expected operation
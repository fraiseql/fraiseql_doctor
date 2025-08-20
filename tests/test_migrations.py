"""Test database migrations work correctly."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text


@pytest.mark.skip("Migration test needs database-level access - to be fixed later")
async def test_migration_up_and_down(fresh_db_session):
    """Test that migrations can be applied and rolled back."""
    # Get Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Start with a clean database by first downgrading everything  
    command.downgrade(alembic_cfg, "base")
    
    # Verify no tables initially
    result = await fresh_db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
    """))
    tables = [row[0] for row in result]
    assert len(tables) == 0, "Should start with no tables"
    
    # Test migration up
    command.upgrade(alembic_cfg, "head")
    
    # Verify tables exist
    result = await fresh_db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
    """))
    tables = [row[0] for row in result]
    
    expected_tables = ['tb_query', 'tb_endpoint', 'tb_execution', 'tb_health_check', 'tb_schedule']
    for table in expected_tables:
        assert table in tables, f"Table {table} should exist after migration"
    
    # Test migration down
    command.downgrade(alembic_cfg, "base")
    
    # Verify tables are gone
    result = await fresh_db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
    """))
    tables = [row[0] for row in result]
    assert len(tables) == 0, "All tables should be removed after downgrade"


async def test_migration_idempotency(fresh_db_session):
    """Test that running migrations multiple times is safe."""
    alembic_cfg = Config("alembic.ini")
    
    # Run migration twice
    command.upgrade(alembic_cfg, "head")
    command.upgrade(alembic_cfg, "head")  # Should not fail
    
    # Verify state is still correct
    result = await fresh_db_session.execute(text("SELECT COUNT(*) FROM alembic_version"))
    version_count = result.scalar()
    assert version_count == 1, "Should have exactly one version record"
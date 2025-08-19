"""Test database migrations work correctly."""
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text


async def test_migration_up_and_down(test_engine):
    """Test that migrations can be applied and rolled back."""
    # Get Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Test migration up
    command.upgrade(alembic_cfg, "head")
    
    # Verify tables exist
    async with test_engine.connect() as conn:
        result = await conn.execute(text("""
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
    async with test_engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
        """))
        tables = [row[0] for row in result]
        assert len(tables) == 0, "All tables should be removed after downgrade"


async def test_migration_idempotency(test_engine):
    """Test that running migrations multiple times is safe."""
    alembic_cfg = Config("alembic.ini")
    
    # Run migration twice
    command.upgrade(alembic_cfg, "head")
    command.upgrade(alembic_cfg, "head")  # Should not fail
    
    # Verify state is still correct
    async with test_engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
        version_count = result.scalar()
        assert version_count == 1, "Should have exactly one version record"
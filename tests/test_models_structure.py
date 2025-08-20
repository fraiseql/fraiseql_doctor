"""Test database model structure and relationships."""
import pytest
from sqlalchemy import text
from fraiseql_doctor.models.base import Base
from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.models.health_check import HealthCheck


async def test_query_model_structure(db_session):
    """Test Query model has required fields and constraints."""
    # Check table exists
    result = await db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'tb_query'
    """))
    assert result.scalar() == 'tb_query'
    
    # Check required columns exist
    result = await db_session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'tb_query'
    """))
    columns = {row[0] for row in result}
    required_columns = {
        'pk_query', 'name', 'description', 'query_text', 'variables',
        'expected_complexity_score', 'tags', 'is_active', 'created_at',
        'updated_at', 'created_by', 'query_metadata'
    }
    assert required_columns.issubset(columns)
    
    # Check unique constraint on name
    result = await db_session.execute(text("""
        SELECT constraint_name FROM information_schema.table_constraints 
        WHERE table_schema = 'public' AND table_name = 'tb_query' 
        AND constraint_type = 'UNIQUE'
    """))
    constraints = [row[0] for row in result]
    assert any('name' in constraint.lower() for constraint in constraints)


async def test_endpoint_model_structure(db_session):
    """Test Endpoint model has required fields and constraints."""
    # Check table exists
    result = await db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'tb_endpoint'
    """))
    assert result.scalar() == 'tb_endpoint'
    
    # Check required columns exist
    result = await db_session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'tb_endpoint'
    """))
    columns = {row[0] for row in result}
    required_columns = {
        'pk_endpoint', 'name', 'url', 'auth_type', 'auth_config',
        'headers', 'timeout_seconds', 'max_retries', 'retry_delay_seconds',
        'is_active', 'created_at', 'updated_at', 'last_health_check'
    }
    assert required_columns.issubset(columns)


async def test_execution_model_relationships(db_session):
    """Test Execution model has proper foreign key relationships."""
    # Check foreign key constraints
    result = await db_session.execute(text("""
        SELECT tc.constraint_name, ccu.table_name as foreign_table_name
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
          AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name='tb_execution'
    """))
    
    foreign_tables = {row[1] for row in result}
    assert 'tb_query' in foreign_tables
    assert 'tb_endpoint' in foreign_tables


async def test_health_check_model_structure(db_session):
    """Test HealthCheck model has required fields and constraints."""
    # Check table exists
    result = await db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'tb_health_check'
    """))
    assert result.scalar() == 'tb_health_check'
    
    # Check required columns exist
    result = await db_session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'tb_health_check'
    """))
    columns = {row[0] for row in result}
    required_columns = {
        'pk_health_check', 'fk_endpoint', 'check_time', 'is_healthy',
        'response_time_ms', 'error_message', 'available_operations',
        'schema_hash', 'check_metadata'
    }
    assert required_columns.issubset(columns)


async def test_all_expected_tables_exist(db_session):
    """Test that all expected tables exist in the database."""
    result = await db_session.execute(text("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE 'tb_%'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    
    expected_tables = [
        'tb_endpoint', 'tb_execution', 'tb_health_check', 
        'tb_query', 'tb_schedule'
    ]
    
    for table in expected_tables:
        assert table in tables, f"Table {table} should exist"


async def test_performance_indexes_exist(db_session):
    """Test that performance indexes were created."""
    result = await db_session.execute(text("""
        SELECT indexname FROM pg_indexes 
        WHERE tablename LIKE 'tb_%' AND indexname LIKE 'idx_%'
        ORDER BY indexname
    """))
    indexes = [row[0] for row in result]
    
    # Check some key indexes exist
    expected_indexes = [
        'idx_query_name',
        'idx_query_tags_gin',
        'idx_endpoint_name',
        'idx_execution_query',
        'idx_execution_endpoint'
    ]
    
    for index in expected_indexes:
        assert index in indexes, f"Index {index} should exist"
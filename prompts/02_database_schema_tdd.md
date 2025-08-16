# Phase 2: TDD Database Schema Design
**Agent: Test-Driven Database Architect**

## Objective
Design and implement a comprehensive database schema using Test-Driven Development, where every model, relationship, and constraint is defined by failing tests FIRST, ensuring robust data integrity and optimal performance.

## 🔄 TDD Database Development Workflow

### Step 1: Schema Behavior Tests (RED Phase)
Write failing tests that define how the database should behave BEFORE creating any models.

#### 1.1 Model Existence and Structure Tests
```python
# tests/test_models_structure.py - Write FIRST
"""Test database model structure and relationships."""
import pytest
from sqlalchemy import inspect
from fraiseql_doctor.models.base import Base
from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.endpoint import Endpoint
from fraiseql_doctor.models.execution import Execution
from fraiseql_doctor.models.health_check import HealthCheck

async def test_query_model_structure(test_engine):
    """Test Query model has required fields and constraints."""
    async with test_engine.connect() as conn:
        inspector = inspect(conn.sync_engine)
        
        # Table should exist
        assert 'tb_query' in inspector.get_table_names()
        
        # Required columns should exist
        columns = {col['name'] for col in inspector.get_columns('tb_query')}
        required_columns = {
            'pk_query', 'name', 'description', 'query_text', 'variables',
            'expected_complexity_score', 'tags', 'is_active', 'created_at',
            'updated_at', 'created_by', 'metadata'
        }
        assert required_columns.issubset(columns)
        
        # Primary key constraint
        pk_constraint = inspector.get_pk_constraint('tb_query')
        assert pk_constraint['constrained_columns'] == ['pk_query']
        
        # Unique constraints
        unique_constraints = inspector.get_unique_constraints('tb_query')
        name_unique = any(
            constraint['column_names'] == ['name'] 
            for constraint in unique_constraints
        )
        assert name_unique, "Query name should be unique"

async def test_endpoint_model_structure(test_engine):
    """Test Endpoint model has required fields and constraints."""
    async with test_engine.connect() as conn:
        inspector = inspect(conn.sync_engine)
        
        assert 'tb_endpoint' in inspector.get_table_names()
        
        columns = {col['name'] for col in inspector.get_columns('tb_endpoint')}
        required_columns = {
            'pk_endpoint', 'name', 'url', 'auth_type', 'auth_config',
            'headers', 'timeout_seconds', 'max_retries', 'retry_delay_seconds',
            'is_active', 'created_at', 'updated_at', 'last_health_check'
        }
        assert required_columns.issubset(columns)

async def test_execution_model_relationships(test_engine):
    """Test Execution model has proper foreign key relationships."""
    async with test_engine.connect() as conn:
        inspector = inspect(conn.sync_engine)
        
        fk_constraints = inspector.get_foreign_keys('tb_execution')
        
        # Should have foreign keys to query and endpoint
        fk_tables = {fk['referred_table'] for fk in fk_constraints}
        assert 'tb_query' in fk_tables
        assert 'tb_endpoint' in fk_tables
        
        # Check cascade behavior
        for fk in fk_constraints:
            if fk['referred_table'] == 'tb_query':
                assert fk['options']['ondelete'] == 'CASCADE'
```

#### 1.2 Data Integrity Tests
```python
# tests/test_data_integrity.py - Write FIRST
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
```

#### 1.3 Performance Requirement Tests
```python
# tests/test_database_performance.py - Write FIRST
"""Test database performance requirements."""
import pytest
import time
from sqlalchemy import select, text
from fraiseql_doctor.models.query import Query
from fraiseql_doctor.models.execution import Execution

@pytest.mark.performance
async def test_query_list_performance(db_session):
    """Test that listing queries meets performance requirements."""
    # Create test data
    queries = []
    for i in range(100):
        query = Query(
            name=f"perf-test-{i}",
            query_text=f"query Test{i} {{ user(id: \"{i}\") {{ id name }} }}",
            tags=[f"tag-{i % 5}"],  # Some overlapping tags
            created_by="perf-test"
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
    pass

async def test_jsonb_query_performance(db_session):
    """Test JSONB queries are properly indexed and performant."""
    # Create queries with searchable tags
    queries = []
    for i in range(50):
        query = Query(
            name=f"jsonb-test-{i}",
            query_text="query { test }",
            tags=["performance", f"category-{i % 3}"],
            metadata={"complexity": i % 10, "category": f"cat-{i % 3}"},
            created_by="jsonb-test"
        )
        queries.append(query)
    
    db_session.add_all(queries)
    await db_session.commit()
    
    # Test tag-based search performance
    start_time = time.time()
    result = await db_session.execute(
        select(Query).where(Query.tags.contains(["performance"]))
    )
    tagged_queries = result.scalars().all()
    search_time = time.time() - start_time
    
    assert len(tagged_queries) == 50
    assert search_time < 0.05  # Should be very fast with GIN index
```

### Step 2: Model Implementation (GREEN Phase)
Implement minimal models to make tests pass.

#### 2.1 Base Model
```python
# src/fraiseql_doctor/models/base.py
"""Base SQLAlchemy model with common functionality."""
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""
    type_annotation_map = {
        dict[str, Any]: JSONB,
        list[str]: JSONB,
        UUID: PG_UUID(as_uuid=True),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
```

#### 2.2 Query Model
```python
# src/fraiseql_doctor/models/query.py
"""Query storage model."""
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Query(Base, TimestampMixin):
    """Stored GraphQL/FraiseQL query model."""
    __tablename__ = "tb_query"

    pk_query: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict[str, Any]] = mapped_column(default=dict)
    expected_complexity_score: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[str | None] = mapped_column(String(255))
    metadata: Mapped[dict[str, Any]] = mapped_column(default=dict)

    # Relationships
    executions = relationship("Execution", back_populates="query", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="query", cascade="all, delete-orphan")
```

#### 2.3 Endpoint Model
```python
# src/fraiseql_doctor/models/endpoint.py
"""Endpoint configuration model."""
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Endpoint(Base, TimestampMixin):
    """GraphQL endpoint configuration model."""
    __tablename__ = "tb_endpoint"

    pk_endpoint: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    auth_type: Mapped[str] = mapped_column(String(50), default="none")
    auth_config: Mapped[dict[str, Any]] = mapped_column(default=dict)
    headers: Mapped[dict[str, Any]] = mapped_column(default=dict)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_seconds: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_health_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    executions = relationship("Execution", back_populates="endpoint", cascade="all, delete-orphan")
    health_checks = relationship("HealthCheck", back_populates="endpoint", cascade="all, delete-orphan")
```

#### 2.4 Execution Model
```python
# src/fraiseql_doctor/models/execution.py
"""Query execution tracking model."""
from typing import Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Execution(Base):
    """Query execution history model."""
    __tablename__ = "tb_execution"

    pk_execution: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fk_query: Mapped[UUID] = mapped_column(ForeignKey("tb_query.pk_query", ondelete="CASCADE"))
    fk_endpoint: Mapped[UUID] = mapped_column(ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"))
    execution_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    execution_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, success, error, timeout
    response_time_ms: Mapped[int | None] = mapped_column(Integer)
    response_size_bytes: Mapped[int | None] = mapped_column(Integer)
    actual_complexity_score: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    error_code: Mapped[str | None] = mapped_column(String(50))
    response_data: Mapped[dict[str, Any] | None] = mapped_column()
    variables_used: Mapped[dict[str, Any]] = mapped_column(default=dict)
    execution_context: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    query = relationship("Query", back_populates="executions")
    endpoint = relationship("Endpoint", back_populates="executions")
```

### Step 3: Migration Tests (RED Phase)
Test that Alembic migrations work correctly.

#### 3.1 Migration Test Framework
```python
# tests/test_migrations.py - Write FIRST
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
        
        expected_tables = ['tb_query', 'tb_endpoint', 'tb_execution', 'tb_health_check']
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
```

### Step 4: Performance Optimization (GREEN Phase)
Implement indexes and optimizations to make performance tests pass.

#### 4.1 Index Creation Migration
```python
# alembic/versions/002_performance_indexes.py
"""Add performance indexes.

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Add performance indexes."""
    # Query table indexes
    op.create_index('idx_query_name', 'tb_query', ['name'])
    op.create_index('idx_query_tags_gin', 'tb_query', ['tags'], postgresql_using='gin')
    op.create_index('idx_query_active', 'tb_query', ['is_active'], 
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_query_created_by', 'tb_query', ['created_by'])
    op.create_index('idx_query_metadata_gin', 'tb_query', ['metadata'], postgresql_using='gin')
    
    # Endpoint table indexes
    op.create_index('idx_endpoint_name', 'tb_endpoint', ['name'])
    op.create_index('idx_endpoint_active', 'tb_endpoint', ['is_active'],
                   postgresql_where=sa.text('is_active = true'))
    op.create_index('idx_endpoint_health_check', 'tb_endpoint', ['last_health_check'])
    
    # Execution table indexes (for performance queries)
    op.create_index('idx_execution_query', 'tb_execution', ['fk_query'])
    op.create_index('idx_execution_endpoint', 'tb_execution', ['fk_endpoint'])
    op.create_index('idx_execution_status', 'tb_execution', ['status'])
    op.create_index('idx_execution_time', 'tb_execution', ['execution_start'])
    op.create_index('idx_execution_performance', 'tb_execution', ['response_time_ms'],
                   postgresql_where=sa.text("status = 'success'"))
    
    # Composite indexes for common queries
    op.create_index('idx_execution_query_status', 'tb_execution', ['fk_query', 'status'])
    op.create_index('idx_execution_endpoint_time', 'tb_execution', ['fk_endpoint', 'execution_start'])

def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_execution_endpoint_time', table_name='tb_execution')
    op.drop_index('idx_execution_query_status', table_name='tb_execution')
    op.drop_index('idx_execution_performance', table_name='tb_execution')
    op.drop_index('idx_execution_time', table_name='tb_execution')
    op.drop_index('idx_execution_status', table_name='tb_execution')
    op.drop_index('idx_execution_endpoint', table_name='tb_execution')
    op.drop_index('idx_execution_query', table_name='tb_execution')
    op.drop_index('idx_endpoint_health_check', table_name='tb_endpoint')
    op.drop_index('idx_endpoint_active', table_name='tb_endpoint')
    op.drop_index('idx_endpoint_name', table_name='tb_endpoint')
    op.drop_index('idx_query_metadata_gin', table_name='tb_query')
    op.drop_index('idx_query_created_by', table_name='tb_query')
    op.drop_index('idx_query_active', table_name='tb_query')
    op.drop_index('idx_query_tags_gin', table_name='tb_query')
    op.drop_index('idx_query_name', table_name='tb_query')
```

### Step 5: Advanced Features (REFACTOR Phase)
Add sophisticated features while maintaining test coverage.

#### 5.1 Partitioning Tests
```python
# tests/test_partitioning.py - Advanced feature tests
"""Test execution table partitioning for performance."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text

async def test_execution_partitioning_setup(test_engine):
    """Test that execution table can be partitioned by month."""
    # This test defines the requirement for partitioning large execution tables
    async with test_engine.connect() as conn:
        # Check if partitioning is supported
        result = await conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'tb_execution_y2024m01'
            )
        """))
        
        # First month partition should exist or be creatable
        partition_exists = result.scalar()
        
        if not partition_exists:
            # Test partition creation (will be implemented in migration)
            pytest.skip("Partitioning not yet implemented")

@pytest.mark.performance
async def test_large_execution_table_performance(db_session):
    """Test performance with large execution history."""
    # This test will drive the need for partitioning
    # Implementation will need to handle 1M+ execution records efficiently
    pass
```

#### 5.2 Data Validation Tests
```python
# tests/test_data_validation.py - Comprehensive validation tests
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
```

## TDD Success Criteria for Phase 2

### RED Phase Verification ✅
- [ ] Model structure tests written and failing initially
- [ ] Data integrity tests define constraint requirements
- [ ] Performance tests establish benchmarks
- [ ] Migration tests ensure deployment reliability

### GREEN Phase Verification ✅
- [ ] SQLAlchemy models implement exactly what tests require
- [ ] All constraints and relationships work as tested
- [ ] Alembic migrations create schema correctly
- [ ] Performance indexes make benchmark tests pass

### REFACTOR Phase Verification ✅
- [ ] Advanced features like partitioning tested
- [ ] Comprehensive validation schemas implemented
- [ ] Code quality improved while maintaining test coverage
- [ ] Database performance optimized

### Database Quality Gates
- [ ] **Model Structure**: All tables, columns, and constraints exist per tests
- [ ] **Data Integrity**: Unique constraints, foreign keys, and validation work
- [ ] **Performance**: Query benchmarks meet requirements with proper indexing
- [ ] **Migrations**: Alembic up/down migrations work reliably
- [ ] **Relationships**: SQLAlchemy relationships function correctly
- [ ] **JSONB Features**: Tag searches and metadata queries are performant

## Handoff to Phase 3
With database foundation tested and solid, Phase 3 will continue TDD for FraiseQL client:

1. **HTTP Client Tests**: Mock external GraphQL APIs properly
2. **Authentication Tests**: Test all auth types with real scenarios
3. **Error Handling Tests**: Network failures, timeouts, malformed responses
4. **Performance Tests**: Concurrent requests, connection pooling benchmarks

The database schema now provides a tested, reliable foundation for all application data needs.
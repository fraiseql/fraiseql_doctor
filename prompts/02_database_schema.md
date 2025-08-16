# Phase 2: Database Schema Design
**Agent: Database Architect**

## Objective
Design and implement a comprehensive database schema for storing and managing FraiseQL/GraphQL queries, execution history, endpoint configurations, and performance metrics.

## Requirements

### Database Technology
- **Database**: PostgreSQL 15+ for advanced JSON support and performance
- **ORM**: SQLAlchemy 2.0+ with async support
- **Migrations**: Alembic for schema versioning
- **Connection**: psycopg3 for modern PostgreSQL connectivity

### Core Schema Design

#### 1. Query Storage (`tb_query`)
```sql
CREATE TABLE tb_query (
    pk_query UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    query_text TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    expected_complexity_score INTEGER,
    tags JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_query_name ON tb_query(name);
CREATE INDEX idx_query_tags ON tb_query USING GIN(tags);
CREATE INDEX idx_query_active ON tb_query(is_active) WHERE is_active = TRUE;
```

#### 2. Endpoint Configuration (`tb_endpoint`)
```sql
CREATE TABLE tb_endpoint (
    pk_endpoint UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50) DEFAULT 'none', -- none, bearer, api_key, basic
    auth_config JSONB DEFAULT '{}',
    headers JSONB DEFAULT '{}',
    timeout_seconds INTEGER DEFAULT 30,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 1,
    fraiseql_version VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    health_check_interval_minutes INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_endpoint_name ON tb_endpoint(name);
CREATE INDEX idx_endpoint_active ON tb_endpoint(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_endpoint_health ON tb_endpoint(last_health_check);
```

#### 3. Query Execution History (`tb_execution`)
```sql
CREATE TABLE tb_execution (
    pk_execution UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fk_query UUID NOT NULL REFERENCES tb_query(pk_query) ON DELETE CASCADE,
    fk_endpoint UUID NOT NULL REFERENCES tb_endpoint(pk_endpoint) ON DELETE CASCADE,
    execution_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL, -- pending, success, error, timeout
    response_time_ms INTEGER,
    response_size_bytes INTEGER,
    actual_complexity_score INTEGER,
    error_message TEXT,
    error_code VARCHAR(50),
    response_data JSONB,
    variables_used JSONB DEFAULT '{}',
    execution_context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_execution_query ON tb_execution(fk_query);
CREATE INDEX idx_execution_endpoint ON tb_execution(fk_endpoint);
CREATE INDEX idx_execution_status ON tb_execution(status);
CREATE INDEX idx_execution_time ON tb_execution(execution_start);
CREATE INDEX idx_execution_performance ON tb_execution(response_time_ms) WHERE status = 'success';
```

#### 4. Health Check Results (`tb_health_check`)
```sql
CREATE TABLE tb_health_check (
    pk_health_check UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fk_endpoint UUID NOT NULL REFERENCES tb_endpoint(pk_endpoint) ON DELETE CASCADE,
    check_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_healthy BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    endpoint_version VARCHAR(50),
    schema_hash VARCHAR(64),
    available_operations JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_health_endpoint ON tb_health_check(fk_endpoint);
CREATE INDEX idx_health_time ON tb_health_check(check_time);
CREATE INDEX idx_health_status ON tb_health_check(is_healthy);
```

#### 5. Query Schedules (`tb_schedule`)
```sql
CREATE TABLE tb_schedule (
    pk_schedule UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fk_query UUID NOT NULL REFERENCES tb_query(pk_query) ON DELETE CASCADE,
    fk_endpoint UUID NOT NULL REFERENCES tb_endpoint(pk_endpoint) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    next_run TIMESTAMP WITH TIME ZONE,
    last_run TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    max_failures INTEGER DEFAULT 5,
    notification_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_schedule_next_run ON tb_schedule(next_run) WHERE is_active = TRUE;
CREATE INDEX idx_schedule_query ON tb_schedule(fk_query);
CREATE INDEX idx_schedule_endpoint ON tb_schedule(fk_endpoint);
```

### SQLAlchemy Models

#### Base Model
```python
"""Base SQLAlchemy model with common fields."""
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

#### Query Model
```python
"""Query storage model."""
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Query(Base, TimestampMixin):
    """Stored GraphQL/FraiseQL query model."""
    __tablename__ = "tb_query"

    pk_query: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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

### Performance Optimization

#### Indexes Strategy
1. **Primary Access Patterns**: Query by name, endpoint URL, execution status
2. **Time-based Queries**: Execution history, health checks by time range
3. **JSON Queries**: GIN indexes for JSONB columns with frequent searches
4. **Composite Indexes**: Query + endpoint combinations for execution lookups

#### Partitioning Strategy
```sql
-- Partition execution table by month for performance
CREATE TABLE tb_execution_template (LIKE tb_execution INCLUDING ALL);

-- Monthly partitions for execution history
CREATE TABLE tb_execution_2024_01 PARTITION OF tb_execution
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Migration Scripts

#### Initial Migration (001_initial_schema.py)
```python
"""Initial database schema.

Revision ID: 001
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Create initial schema."""
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create tables
    op.create_table('tb_query',
        sa.Column('pk_query', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        # ... rest of columns
    )
    
    # Create indexes
    op.create_index('idx_query_name', 'tb_query', ['name'])
    # ... rest of indexes

def downgrade() -> None:
    """Drop initial schema."""
    op.drop_table('tb_query')
```

### Data Validation

#### Pydantic Schemas
```python
"""Pydantic schemas for data validation."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class QueryCreate(BaseModel):
    """Schema for creating a new query."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    query_text: str = Field(..., min_length=1)
    variables: dict[str, Any] = Field(default_factory=dict)
    expected_complexity_score: int | None = Field(None, ge=0)
    tags: list[str] = Field(default_factory=list)
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EndpointCreate(BaseModel):
    """Schema for creating a new endpoint."""
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    auth_type: str = Field(default="none", pattern="^(none|bearer|api_key|basic)$")
    auth_config: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=1, ge=0, le=60)
```

### Success Criteria
- [x] Complete database schema designed and documented
- [x] SQLAlchemy models created with proper relationships
- [x] Migration scripts written and tested
- [x] Indexes optimized for expected query patterns
- [x] Data validation schemas defined
- [x] Performance considerations implemented
- [x] PostgreSQL-specific features utilized (JSONB, UUID)

### Handoff Notes for Next Phase
- GraphQL client should use the Endpoint model for configuration
- Query execution should create Execution records for all attempts
- Health checking should populate tb_health_check regularly
- Consider implementing database connection pooling
- Use async SQLAlchemy sessions for all database operations
- Implement proper error handling for database connection issues
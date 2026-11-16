"""Initial database schema

Revision ID: 1cbd4bbc07cb
Revises:
Create Date: 2025-08-16 17:36:01.479286

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1cbd4bbc07cb"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tb_query table
    op.create_table(
        "tb_query",
        sa.Column("pk_query", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("variables", postgresql.JSONB(), server_default="{}"),
        sa.Column("expected_complexity_score", sa.Integer()),
        sa.Column("tags", postgresql.JSONB(), server_default="[]"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_by", sa.String(255)),
        sa.Column("query_metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create tb_endpoint table
    op.create_table(
        "tb_endpoint",
        sa.Column("pk_endpoint", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("auth_type", sa.String(50), server_default="none"),
        sa.Column("auth_config", postgresql.JSONB(), server_default="{}"),
        sa.Column("headers", postgresql.JSONB(), server_default="{}"),
        sa.Column("timeout_seconds", sa.Integer(), server_default="30"),
        sa.Column("max_retries", sa.Integer(), server_default="3"),
        sa.Column("retry_delay_seconds", sa.Integer(), server_default="1"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("last_health_check", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create tb_execution table
    op.create_table(
        "tb_execution",
        sa.Column("pk_execution", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "fk_query",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tb_query.pk_query", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fk_endpoint",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("execution_start", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("execution_end", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("response_time_ms", sa.Integer()),
        sa.Column("response_size_bytes", sa.Integer()),
        sa.Column("actual_complexity_score", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("error_code", sa.String(50)),
        sa.Column("response_data", postgresql.JSONB()),
        sa.Column("variables_used", postgresql.JSONB(), server_default="{}"),
        sa.Column("execution_context", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Create tb_health_check table
    op.create_table(
        "tb_health_check",
        sa.Column("pk_health_check", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "fk_endpoint",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_time", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("is_healthy", sa.Boolean(), nullable=False),
        sa.Column("response_time_ms", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column("available_operations", postgresql.JSONB(), server_default="[]"),
        sa.Column("schema_hash", sa.String(64)),
        sa.Column("check_metadata", postgresql.JSONB(), server_default="{}"),
    )

    # Create tb_schedule table
    op.create_table(
        "tb_schedule",
        sa.Column("pk_schedule", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "fk_query",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tb_query.pk_query", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fk_endpoint",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tb_endpoint.pk_endpoint", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("cron_expression", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("next_run", sa.DateTime(timezone=True)),
        sa.Column("last_run", sa.DateTime(timezone=True)),
        sa.Column("variables_override", postgresql.JSONB(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tb_schedule")
    op.drop_table("tb_health_check")
    op.drop_table("tb_execution")
    op.drop_table("tb_endpoint")
    op.drop_table("tb_query")

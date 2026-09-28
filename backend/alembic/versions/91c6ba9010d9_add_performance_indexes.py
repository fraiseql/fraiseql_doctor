"""Add performance indexes

Revision ID: 91c6ba9010d9
Revises: 1cbd4bbc07cb
Create Date: 2025-08-16 17:37:14.604671

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "91c6ba9010d9"
down_revision: str | Sequence[str] | None = "1cbd4bbc07cb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add performance indexes."""
    # Query table indexes
    op.create_index("idx_query_name", "tb_query", ["name"])
    op.create_index("idx_query_tags_gin", "tb_query", ["tags"], postgresql_using="gin")
    op.create_index(
        "idx_query_active", "tb_query", ["is_active"], postgresql_where=sa.text("is_active = true")
    )
    op.create_index("idx_query_created_by", "tb_query", ["created_by"])
    op.create_index(
        "idx_query_metadata_gin", "tb_query", ["query_metadata"], postgresql_using="gin"
    )

    # Endpoint table indexes
    op.create_index("idx_endpoint_name", "tb_endpoint", ["name"])
    op.create_index(
        "idx_endpoint_active",
        "tb_endpoint",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_endpoint_health_check", "tb_endpoint", ["last_health_check"])

    # Execution table indexes (for performance queries)
    op.create_index("idx_execution_query", "tb_execution", ["fk_query"])
    op.create_index("idx_execution_endpoint", "tb_execution", ["fk_endpoint"])
    op.create_index("idx_execution_status", "tb_execution", ["status"])
    op.create_index("idx_execution_time", "tb_execution", ["execution_start"])
    op.create_index(
        "idx_execution_performance",
        "tb_execution",
        ["response_time_ms"],
        postgresql_where=sa.text("status = 'success'"),
    )

    # Composite indexes for common queries
    op.create_index("idx_execution_query_status", "tb_execution", ["fk_query", "status"])
    op.create_index(
        "idx_execution_endpoint_time", "tb_execution", ["fk_endpoint", "execution_start"]
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("idx_execution_endpoint_time", table_name="tb_execution")
    op.drop_index("idx_execution_query_status", table_name="tb_execution")
    op.drop_index("idx_execution_performance", table_name="tb_execution")
    op.drop_index("idx_execution_time", table_name="tb_execution")
    op.drop_index("idx_execution_status", table_name="tb_execution")
    op.drop_index("idx_execution_endpoint", table_name="tb_execution")
    op.drop_index("idx_execution_query", table_name="tb_execution")
    op.drop_index("idx_endpoint_health_check", table_name="tb_endpoint")
    op.drop_index("idx_endpoint_active", table_name="tb_endpoint")
    op.drop_index("idx_endpoint_name", table_name="tb_endpoint")
    op.drop_index("idx_query_metadata_gin", table_name="tb_query")
    op.drop_index("idx_query_created_by", table_name="tb_query")
    op.drop_index("idx_query_active", table_name="tb_query")
    op.drop_index("idx_query_tags_gin", table_name="tb_query")
    op.drop_index("idx_query_name", table_name="tb_query")

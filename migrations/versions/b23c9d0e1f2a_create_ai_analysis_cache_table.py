"""create ai_analysis_cache table.

Revision ID: b23c9d0e1f2a
Revises: a12b8c9d0e1f
Create Date: 2026-11-13 14:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b23c9d0e1f2a"
down_revision: str | Sequence[str] | None = "a12b8c9d0e1f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema with ai_analysis_cache table."""
    op.create_table(
        "ai_analysis_cache",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("cost_center_id", sa.Uuid(), nullable=True),
        sa.Column("accounting_account_id", sa.Uuid(), nullable=True),
        sa.Column("data_hash", sa.String(length=64), nullable=False),
        sa.Column("summary_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_analysis_cache_cache_key"),
        "ai_analysis_cache",
        ["cache_key"],
        unique=True,
    )
    op.create_index(
        op.f("ix_ai_analysis_cache_period"),
        "ai_analysis_cache",
        ["period"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_analysis_cache_expires_at"),
        "ai_analysis_cache",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_analysis_cache_cost_center_id"),
        "ai_analysis_cache",
        ["cost_center_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ai_analysis_cache_accounting_account_id"),
        "ai_analysis_cache",
        ["accounting_account_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema by removing ai_analysis_cache table."""
    op.drop_index(
        op.f("ix_ai_analysis_cache_accounting_account_id"),
        table_name="ai_analysis_cache",
    )
    op.drop_index(
        op.f("ix_ai_analysis_cache_cost_center_id"),
        table_name="ai_analysis_cache",
    )
    op.drop_index(
        op.f("ix_ai_analysis_cache_expires_at"),
        table_name="ai_analysis_cache",
    )
    op.drop_index(
        op.f("ix_ai_analysis_cache_period"),
        table_name="ai_analysis_cache",
    )
    op.drop_index(
        op.f("ix_ai_analysis_cache_cache_key"),
        table_name="ai_analysis_cache",
    )
    op.drop_table("ai_analysis_cache")

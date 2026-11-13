"""add accounting accounts table and allocation columns.

Revision ID: a12b8c9d0e1f
Revises: e01c6b0fe401
Create Date: 2026-11-13 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a12b8c9d0e1f"
down_revision: str | Sequence[str] | None = "e01c6b0fe401"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accounting_accounts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "description", sa.String(length=500), nullable=False, server_default=""
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_accounting_accounts_code"),
        "accounting_accounts",
        ["code"],
        unique=True,
    )

    op.add_column(
        "contract_default_allocations",
        sa.Column("accounting_account_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        op.f("ix_contract_default_allocations_accounting_account_id"),
        "contract_default_allocations",
        ["accounting_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_contract_default_allocations_accounting_account_id",
        "contract_default_allocations",
        "accounting_accounts",
        ["accounting_account_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "measurement_allocation_entries",
        sa.Column("accounting_account_id", sa.Uuid(), nullable=True),
    )
    op.create_index(
        op.f("ix_measurement_allocation_entries_accounting_account_id"),
        "measurement_allocation_entries",
        ["accounting_account_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_measurement_allocation_entries_accounting_account_id",
        "measurement_allocation_entries",
        "accounting_accounts",
        ["accounting_account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_measurement_allocation_entries_accounting_account_id",
        "measurement_allocation_entries",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_measurement_allocation_entries_accounting_account_id"),
        table_name="measurement_allocation_entries",
    )
    op.drop_column("measurement_allocation_entries", "accounting_account_id")

    op.drop_constraint(
        "fk_contract_default_allocations_accounting_account_id",
        "contract_default_allocations",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_contract_default_allocations_accounting_account_id"),
        table_name="contract_default_allocations",
    )
    op.drop_column("contract_default_allocations", "accounting_account_id")

    op.drop_index(
        op.f("ix_accounting_accounts_code"), table_name="accounting_accounts"
    )
    op.drop_table("accounting_accounts")

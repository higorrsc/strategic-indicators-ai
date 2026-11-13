"""Pydantic presentation schemas for Accounting Accounts endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountingAccountCreateRequest(BaseModel):
    """Request payload to register a new accounting account."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        description="Hierarchical dot-separated accounting account code (e.g. 3.1.01).",
        examples=["3.1.01"],
    )
    name: str = Field(
        description="Descriptive account name.",
        examples=["Software Licenses"],
    )
    description: str = Field(
        default="",
        description="Optional detailed description.",
        examples=["SaaS and on-premise software licenses."],
    )


class AccountingAccountResponse(BaseModel):
    """Response schema representing an accounting account."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    code: str
    name: str
    description: str
    is_active: bool


class CostCenterAccountSpendResponse(BaseModel):
    """Response schema for expenditure allocated to an accounting account."""

    model_config = ConfigDict(frozen=True)

    accounting_account_id: UUID | None
    account_code: str | None
    account_name: str | None
    spent_amount: Decimal
    share_pct: Decimal


class CostCenterAccountingBreakdownResponse(BaseModel):
    """Response schema representing a cost center's spend partitioned by account."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    period: str
    total_spent: Decimal
    accounts: list[CostCenterAccountSpendResponse]

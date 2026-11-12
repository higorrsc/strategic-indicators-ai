"""Pydantic presentation schemas for Budgeting endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CostCenterCreateRequest(BaseModel):
    """Request payload to create a new cost center."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(description="Hierarchical cost center code (e.g., 1.0 or 1.1).")
    name: str = Field(description="Human-readable cost center name.")
    parent_id: UUID | None = Field(
        default=None, description="Optional parent cost center ID."
    )


class CostCenterResponse(BaseModel):
    """Response schema representing a cost center."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    code: str
    name: str
    parent_id: UUID | None
    is_active: bool


class BudgetTargetSetRequest(BaseModel):
    """Request payload to define a budget target."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    period: str = Field(description="Fiscal period in YYYY-MM format.")
    category: str = Field(description="Budget expense category (e.g. OPEX).")
    amount: Decimal = Field(ge=Decimal("0"), description="Planned monetary amount.")
    currency: str = Field(default="USD", description="Currency code.")


class BudgetTargetResponse(BaseModel):
    """Response schema representing a recorded budget target."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    cost_center_id: UUID
    period: str
    category: str
    amount: Decimal
    currency: str


class HierarchyBudgetResponse(BaseModel):
    """Response schema representing aggregated hierarchical budget."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    cost_center_code: str
    period: str
    direct_total: Decimal
    consolidated_total: Decimal
    currency: str

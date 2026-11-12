"""Pydantic presentation schemas for Cost Allocation endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AllocationShareSchema(BaseModel):
    """Schema representing an allocation percentage share for a cost center."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    percentage: Decimal = Field(
        gt=Decimal("0"),
        le=Decimal("100"),
        description="Percentage share (0.01 to 100.00).",
    )


class ContractCreateRequest(BaseModel):
    """Request payload to register a supplier contract."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(description="Unique contract code e.g. CT-2026-001.")
    supplier_id: UUID = Field(description="Associated supplier UUID.")
    title: str = Field(description="Contract title or description.")
    default_allocations: list[AllocationShareSchema] = Field(
        default_factory=list,
        description="Optional default allocation distribution across centers.",
    )


class ContractResponse(BaseModel):
    """Response schema representing a supplier contract."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    code: str
    supplier_id: UUID
    title: str
    default_allocations: list[AllocationShareSchema]
    is_active: bool


class AllocationEntryResponse(BaseModel):
    """Response schema for a single calculated allocation line."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    percentage: Decimal
    amount: Decimal
    currency: str


class MeasurementSubmitRequest(BaseModel):
    """Request payload to submit a financial measurement."""

    model_config = ConfigDict(frozen=True)

    contract_id: UUID
    period: str = Field(description="Fiscal period in YYYY-MM format.")
    description: str = Field(description="Measurement description or service note.")
    gross_amount: Decimal = Field(gt=Decimal("0"), description="Total monetary amount.")
    currency: str = Field(default="USD", description="Currency code.")
    allocation_override: list[AllocationShareSchema] | None = Field(
        default=None,
        description="Optional override replacing contract default allocations.",
    )


class MeasurementResponse(BaseModel):
    """Response schema representing a financial measurement."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    contract_id: UUID
    period: str
    description: str
    gross_amount: Decimal
    currency: str
    state: str
    entries: list[AllocationEntryResponse]

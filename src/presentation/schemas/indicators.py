"""Pydantic presentation schemas for Budget Indicators and Simulations."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CostCenterIndicatorResponse(BaseModel):
    """Response schema for a single cost center's variance metrics."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    cost_center_code: str
    period: str
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    execution_rate: Decimal
    status: str
    currency: str


class PeriodIndicatorsResponse(BaseModel):
    """Response schema for consolidated period indicators."""

    model_config = ConfigDict(frozen=True)

    period: str
    indicators: list[CostCenterIndicatorResponse]
    total_budgeted: Decimal
    total_actual: Decimal
    total_variance: Decimal
    total_execution_rate: Decimal
    currency: str


class AllocationShiftSchema(BaseModel):
    """Schema specifying an allocation percentage shift between two centers."""

    model_config = ConfigDict(frozen=True)

    from_cost_center_id: UUID
    to_cost_center_id: UUID
    percentage_points: Decimal = Field(
        gt=Decimal("0"),
        le=Decimal("100"),
        description="Percentage points to shift (0.01 to 100.00).",
    )
    contract_id: UUID | None = Field(
        default=None, description="Optional target contract UUID."
    )


class ScenarioSimulateRequest(BaseModel):
    """Request payload to execute a what-if scenario simulation."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(description="Scenario name e.g. '15% Cloud Cost Inflation'.")
    period: str = Field(description="Target fiscal period in YYYY-MM format.")
    contract_inflation: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Map of contract UUID string to percentage inflation (e.g. 15.0).",
    )
    allocation_shifts: list[AllocationShiftSchema] = Field(
        default_factory=list,
        description="List of allocation reallocations between cost centers.",
    )


class CostCenterImpactResponse(BaseModel):
    """Response schema for individual cost center impact under simulation."""

    model_config = ConfigDict(frozen=True)

    cost_center_id: UUID
    cost_center_code: str
    baseline_actual: Decimal
    simulated_actual: Decimal
    delta_actual: Decimal
    baseline_status: str
    simulated_status: str
    new_overrun: bool


class SimulationResultResponse(BaseModel):
    """Response schema representing what-if simulation results."""

    model_config = ConfigDict(frozen=True)

    scenario_name: str
    period: str
    impacts: list[CostCenterImpactResponse]
    new_overruns_count: int
    total_baseline_actual: Decimal
    total_simulated_actual: Decimal
    total_delta: Decimal

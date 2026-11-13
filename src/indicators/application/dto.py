"""Data Transfer Objects for budget indicators and simulations."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CostCenterIndicatorDTO:
    """DTO representing individual cost center performance indicators."""

    cost_center_id: UUID
    cost_center_code: str
    period: str
    budgeted_amount: Decimal
    actual_amount: Decimal
    variance_amount: Decimal
    execution_rate: Decimal
    status: str
    currency: str


@dataclass(frozen=True, slots=True)
class PeriodIndicatorsDTO:
    """DTO representing consolidated period indicators across cost centers."""

    period: str
    indicators: list[CostCenterIndicatorDTO]
    total_budgeted: Decimal
    total_actual: Decimal
    total_variance: Decimal
    total_execution_rate: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class ComputePeriodIndicatorsQuery:
    """Query payload to fetch indicators for a fiscal period."""

    period: str
    cost_center_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AllocationShiftDTO:
    """DTO specifying an allocation shift between two cost centers."""

    from_cost_center_id: UUID
    to_cost_center_id: UUID
    percentage_points: Decimal
    contract_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SimulateScenarioCommand:
    """Command payload to execute a what-if budget simulation."""

    scenario_name: str
    period: str
    contract_cost_adjustments: dict[UUID, Decimal] = field(default_factory=dict)
    allocation_shifts: list[AllocationShiftDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CostCenterImpactDTO:
    """DTO representing differential impact on a cost center."""

    cost_center_id: UUID
    cost_center_code: str
    baseline_actual: Decimal
    simulated_actual: Decimal
    delta_actual: Decimal
    baseline_status: str
    simulated_status: str
    new_overrun: bool
    currency: str


@dataclass(frozen=True, slots=True)
class SimulationResultDTO:
    """DTO representing the complete results of a what-if simulation."""

    scenario_name: str
    period: str
    baseline_indicators: list[CostCenterIndicatorDTO]
    simulated_indicators: list[CostCenterIndicatorDTO]
    impacts: list[CostCenterImpactDTO]


@dataclass(frozen=True, slots=True)
class MaterialityItemDTO:
    """DTO representing an individual ranked materiality item."""

    entity_id: UUID | None
    code: str
    name: str
    level: str
    planned_budget: Decimal | None
    actual_spent: Decimal
    variance: Decimal | None
    metric_value: Decimal
    share_of_total_pct: Decimal
    cumulative_pct: Decimal
    priority: str
    rank: int


@dataclass(frozen=True, slots=True)
class MaterialImpactReportDTO:
    """DTO representing the consolidated materiality and Pareto focus report."""

    period: str
    aggregation_level: str
    focus_metric: str
    cost_center_scope_id: UUID | None
    total_baseline_budget: Decimal | None
    total_baseline_spent: Decimal
    total_baseline_overrun: Decimal
    items: list[MaterialityItemDTO]
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class GenerateMaterialImpactQuery:
    """Query payload to generate a materiality and effort focus report."""

    period: str
    level: str = "cost_center"
    metric: str = "variance"
    cost_center_id: UUID | None = None
    threshold_pct: Decimal | None = None


"""Domain models and value representations for strategic budget indicators."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from src.indicators.domain.types import ActionPriority, AggregationLevel, FocusMetric
from src.shared.domain.value_objects import Money, Percentage, Period


class IndicatorStatus(StrEnum):
    """Budget execution health status categories."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL_OVERRUN = "CRITICAL_OVERRUN"


@dataclass(frozen=True, slots=True)
class CostCenterIndicator:
    """Calculated budget vs actual performance indicator for a cost center."""

    cost_center_id: UUID
    cost_center_code: str
    period: Period
    budgeted_amount: Money
    actual_amount: Money
    variance_amount: Money
    execution_rate: Percentage
    status: IndicatorStatus


@dataclass(frozen=True, slots=True)
class MaterialityCandidate:
    """Raw candidate item evaluated for materiality and effort ranking."""

    entity_id: UUID | None
    code: str
    name: str
    level: AggregationLevel
    actual_spent: Money
    planned_budget: Money | None = None
    variance: Money | None = None


@dataclass(frozen=True, slots=True)
class MaterialityItem:
    """Evaluated materiality item with calculated ranking and action priority."""

    entity_id: UUID | None
    code: str
    name: str
    level: AggregationLevel
    planned_budget: Money | None
    actual_spent: Money
    variance: Money | None
    metric_value: Money
    share_of_total_pct: Decimal
    cumulative_pct: Decimal
    priority: ActionPriority
    rank: int


@dataclass(frozen=True, slots=True)
class MaterialityAnalysisResult:
    """Consolidated outcome of materiality and Pareto effort ranking."""

    metric: FocusMetric
    total_baseline_budget: Money | None
    total_baseline_spent: Money
    total_baseline_overrun: Money
    items: list[MaterialityItem]


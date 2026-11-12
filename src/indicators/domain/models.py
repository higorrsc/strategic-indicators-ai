"""Domain models and value representations for strategic budget indicators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

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

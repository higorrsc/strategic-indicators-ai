"""Domain service for calculating budget execution variance and alert statuses."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.allocation.domain.entities.measurement import (
    Measurement,
    MeasurementState,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.shared.domain.value_objects import Money, Percentage, Period

_WARNING_THRESHOLD = Percentage.from_number("80.00")
_OVERRUN_THRESHOLD = Percentage.hundred()


class BudgetVarianceCalculator:
    """Calculates deterministic variance, consumption rate, and status indicators."""

    @classmethod
    def calculate(
        cls,
        cost_center_id: UUID,
        cost_center_code: str,
        period: Period,
        budgeted_amount: Money,
        actual_amount: Money,
    ) -> CostCenterIndicator:
        """Calculate indicator for a single pair of budgeted and actual amounts.

        Args:
            cost_center_id: Cost center UUID.
            cost_center_code: Formatted hierarchical code.
            period: Target fiscal period.
            budgeted_amount: Planned monetary budget.
            actual_amount: Actual approved executed expenses.

        Returns:
            CostCenterIndicator: Computed performance metric.
        """
        variance = actual_amount - budgeted_amount

        if budgeted_amount.amount > Decimal("0.00"):
            ratio = actual_amount.amount / budgeted_amount.amount
            execution_rate = Percentage.from_ratio(ratio)
            if execution_rate <= _WARNING_THRESHOLD:
                status = IndicatorStatus.NORMAL
            elif execution_rate <= _OVERRUN_THRESHOLD:
                status = IndicatorStatus.WARNING
            else:
                status = IndicatorStatus.CRITICAL_OVERRUN
        elif actual_amount.amount > Decimal("0.00"):
            execution_rate = Percentage.from_number("999.00")
            status = IndicatorStatus.CRITICAL_OVERRUN
        else:
            execution_rate = Percentage.zero()
            status = IndicatorStatus.NORMAL

        return CostCenterIndicator(
            cost_center_id=cost_center_id,
            cost_center_code=cost_center_code,
            period=period,
            budgeted_amount=budgeted_amount,
            actual_amount=actual_amount,
            variance_amount=variance,
            execution_rate=execution_rate,
            status=status,
        )

    @classmethod
    def calculate_from_records(
        cls,
        cost_center_id: UUID,
        cost_center_code: str,
        period: Period,
        budgets: list[BudgetTarget],
        measurements: list[Measurement],
        currency: str = "USD",
    ) -> CostCenterIndicator:
        """Calculate indicator from raw budget targets and approved measurements.

        Args:
            cost_center_id: Cost center UUID.
            cost_center_code: Formatted code.
            period: Target period.
            budgets: List of planned budget targets.
            measurements: List of measurements.
            currency: Currency code.

        Returns:
            CostCenterIndicator: Computed performance metric.
        """
        # Sum budgeted amounts for this cost center & period
        relevant_budgets = [
            b
            for b in budgets
            if b.cost_center_id == cost_center_id and b.period == period
        ]
        budgeted_sum = sum(
            (b.amount for b in relevant_budgets),
            Money.zero(currency),
        )

        # Sum allocated amounts from approved measurements for this cost center & period
        actual_entries: list[Money] = []
        for m in measurements:
            if m.period == period and m.state == MeasurementState.APPROVED:
                for entry in m.entries:
                    if entry.cost_center_id == cost_center_id:
                        actual_entries.append(entry.amount)

        actual_sum = sum(actual_entries, Money.zero(currency))

        return cls.calculate(
            cost_center_id=cost_center_id,
            cost_center_code=cost_center_code,
            period=period,
            budgeted_amount=budgeted_sum,
            actual_amount=actual_sum,
        )

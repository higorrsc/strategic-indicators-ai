"""What-if scenario simulation domain service."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.allocation.domain.entities.contract import AllocationShare
from src.allocation.domain.entities.measurement import (
    Measurement,
    MeasurementState,
)
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.indicators.domain.exceptions import SimulationParameterError
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.indicators.domain.services.variance_calculator import (
    BudgetVarianceCalculator,
)
from src.shared.domain.value_objects import Money, Percentage, Period


@dataclass(frozen=True, slots=True)
class AllocationShift:
    """Specification of an allocation percentage shift between two cost centers."""

    from_cost_center_id: UUID
    to_cost_center_id: UUID
    percentage_points: Percentage
    contract_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CostCenterImpact:
    """Differential impact on a cost center between baseline and simulation."""

    cost_center_id: UUID
    cost_center_code: str
    baseline_actual: Money
    simulated_actual: Money
    delta_actual: Money
    baseline_status: IndicatorStatus
    simulated_status: IndicatorStatus
    new_overrun: bool


@dataclass(frozen=True, slots=True)
class SimulationComparison:
    """Complete simulation result contrasting baseline and simulated states."""

    scenario_name: str
    period: Period
    baseline_indicators: list[CostCenterIndicator]
    simulated_indicators: list[CostCenterIndicator]
    impacts: list[CostCenterImpact]


class WhatIfSimulator:
    """Pure domain service simulating in-memory hypothetical budget scenarios."""

    @classmethod
    def simulate(
        cls,
        scenario_name: str,
        period: Period,
        cost_centers: dict[UUID, str],
        budgets: list[BudgetTarget],
        measurements: list[Measurement],
        contract_cost_adjustments: dict[UUID, Percentage] | None = None,
        allocation_shifts: list[AllocationShift] | None = None,
        currency: str = "USD",
    ) -> SimulationComparison:
        """Execute a what-if scenario simulation without mutating baseline records.

        Args:
            scenario_name: Descriptive name of the hypothetical scenario.
            period: Target fiscal period.
            cost_centers: Map of cost_center_id -> cost_center_code.
            budgets: List of planned budget targets.
            measurements: List of approved baseline measurements.
            contract_cost_adjustments: Map of contract_id -> percentage adjustment.
            allocation_shifts: List of allocation shifts between cost centers.
            currency: Currency code.

        Returns:
            SimulationComparison: Differential comparison table.
        """
        adjustments = contract_cost_adjustments or {}
        shifts = allocation_shifts or []

        # 1. Compute baseline indicators for each cost center
        baseline_indicators: list[CostCenterIndicator] = []
        for cc_id, cc_code in cost_centers.items():
            ind = BudgetVarianceCalculator.calculate_from_records(
                cost_center_id=cc_id,
                cost_center_code=cc_code,
                period=period,
                budgets=budgets,
                measurements=measurements,
                currency=currency,
            )
            baseline_indicators.append(ind)

        # 2. Simulate measurements in-memory
        simulated_measurements: list[Measurement] = []
        for m in measurements:
            if m.period != period or m.state != MeasurementState.APPROVED:
                continue

            # Apply cost adjustment
            factor = Decimal("1.00")
            if m.contract_id in adjustments:
                factor += adjustments[m.contract_id].as_ratio()

            if factor < Decimal("0.00"):
                raise SimulationParameterError(
                    f"Cost factor cannot reduce expense below zero: {factor}."
                )

            new_gross = m.gross_amount * factor

            # Extract existing shares
            shares = [
                AllocationShare(
                    cost_center_id=e.cost_center_id,
                    percentage=e.percentage,
                )
                for e in m.entries
            ]

            # Apply shifts if applicable
            for shift in shifts:
                if shift.contract_id is None or shift.contract_id == m.contract_id:
                    shares = cls._apply_shift_to_shares(shares, shift)

            new_entries = ExactPennyAllocator.allocate(new_gross, shares)

            sim_m = Measurement(
                contract_id=m.contract_id,
                period=m.period,
                description=f"[Simulated] {m.description}",
                gross_amount=new_gross,
                state=MeasurementState.APPROVED,
                entries=new_entries,
            )
            simulated_measurements.append(sim_m)

        # 3. Compute simulated indicators
        simulated_indicators: list[CostCenterIndicator] = []
        baseline_by_id = {ind.cost_center_id: ind for ind in baseline_indicators}
        impacts: list[CostCenterImpact] = []

        for cc_id, cc_code in cost_centers.items():
            sim_ind = BudgetVarianceCalculator.calculate_from_records(
                cost_center_id=cc_id,
                cost_center_code=cc_code,
                period=period,
                budgets=budgets,
                measurements=simulated_measurements,
                currency=currency,
            )
            simulated_indicators.append(sim_ind)

            base_ind = baseline_by_id[cc_id]
            delta = sim_ind.actual_amount - base_ind.actual_amount
            new_overrun = (
                base_ind.status != IndicatorStatus.CRITICAL_OVERRUN
                and sim_ind.status == IndicatorStatus.CRITICAL_OVERRUN
            )

            impacts.append(
                CostCenterImpact(
                    cost_center_id=cc_id,
                    cost_center_code=cc_code,
                    baseline_actual=base_ind.actual_amount,
                    simulated_actual=sim_ind.actual_amount,
                    delta_actual=delta,
                    baseline_status=base_ind.status,
                    simulated_status=sim_ind.status,
                    new_overrun=new_overrun,
                )
            )

        return SimulationComparison(
            scenario_name=scenario_name,
            period=period,
            baseline_indicators=baseline_indicators,
            simulated_indicators=simulated_indicators,
            impacts=impacts,
        )

    @staticmethod
    def _apply_shift_to_shares(
        shares: list[AllocationShare], shift: AllocationShift
    ) -> list[AllocationShare]:
        """Apply percentage shift between from and to cost centers."""
        from_idx = next(
            (
                i
                for i, s in enumerate(shares)
                if s.cost_center_id == shift.from_cost_center_id
            ),
            None,
        )
        if from_idx is None:
            return shares

        from_share = shares[from_idx]
        shift_val = shift.percentage_points.value

        if from_share.percentage.value < shift_val:
            raise SimulationParameterError(
                f"Cannot shift {shift_val}% from cost center "
                f"with only {from_share.percentage.value}%."
            )

        new_from_share = AllocationShare(
            cost_center_id=from_share.cost_center_id,
            percentage=Percentage.from_number(from_share.percentage.value - shift_val),
        )

        to_idx = next(
            (
                i
                for i, s in enumerate(shares)
                if s.cost_center_id == shift.to_cost_center_id
            ),
            None,
        )

        new_shares = list(shares)
        new_shares[from_idx] = new_from_share

        if to_idx is not None:
            to_share = new_shares[to_idx]
            new_shares[to_idx] = AllocationShare(
                cost_center_id=to_share.cost_center_id,
                percentage=Percentage.from_number(
                    to_share.percentage.value + shift_val
                ),
            )
        else:
            new_shares.append(
                AllocationShare(
                    cost_center_id=shift.to_cost_center_id,
                    percentage=Percentage.from_number(shift_val),
                )
            )

        # Remove zero shares if any
        return [s for s in new_shares if s.percentage.value > Decimal("0.00")]

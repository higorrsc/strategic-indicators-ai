"""Use case for simulating what-if budget scenarios."""

from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.indicators.application.dto import (
    CostCenterImpactDTO,
    CostCenterIndicatorDTO,
    SimulateScenarioCommand,
    SimulationResultDTO,
)
from src.indicators.domain.services.simulator import (
    AllocationShift,
    WhatIfSimulator,
)
from src.shared.domain.value_objects import Percentage, Period


class SimulateScenarioUseCase:
    """Orchestrates in-memory execution of what-if budget scenarios."""

    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        budget_repository: BudgetRepository,
        measurement_repository: MeasurementRepository,
    ) -> None:
        """Initialize use case with required repositories.

        Args:
            cost_center_repository: Repository for cost centers.
            budget_repository: Repository for planned budgets.
            measurement_repository: Repository for approved measurements.
        """
        self._cost_center_repository = cost_center_repository
        self._budget_repository = budget_repository
        self._measurement_repository = measurement_repository

    async def execute(self, command: SimulateScenarioCommand) -> SimulationResultDTO:
        """Execute simulation command and return comparison results.

        Args:
            command: Simulation specification payload.

        Returns:
            SimulationResultDTO: Detailed comparative impact metrics.
        """
        period = Period.from_string(command.period)
        all_ccs = await self._cost_center_repository.list_all(active_only=True)
        cc_map = {cc.id: str(cc.code) for cc in all_ccs}

        budgets = await self._budget_repository.list_by_period(period)
        measurements = await self._measurement_repository.list_by_period(period)

        cost_adjustments = {
            cid: Percentage.from_number(pct)
            for cid, pct in command.contract_cost_adjustments.items()
        }

        shifts = [
            AllocationShift(
                from_cost_center_id=s.from_cost_center_id,
                to_cost_center_id=s.to_cost_center_id,
                percentage_points=Percentage.from_number(s.percentage_points),
                contract_id=s.contract_id,
            )
            for s in command.allocation_shifts
        ]

        result = WhatIfSimulator.simulate(
            scenario_name=command.scenario_name,
            period=period,
            cost_centers=cc_map,
            budgets=budgets,
            measurements=measurements,
            contract_cost_adjustments=cost_adjustments,
            allocation_shifts=shifts,
            currency="USD",
        )

        baseline_dtos = [
            CostCenterIndicatorDTO(
                cost_center_id=ind.cost_center_id,
                cost_center_code=ind.cost_center_code,
                period=str(ind.period),
                budgeted_amount=ind.budgeted_amount.amount,
                actual_amount=ind.actual_amount.amount,
                variance_amount=ind.variance_amount.amount,
                execution_rate=ind.execution_rate.value,
                status=ind.status.value,
                currency=ind.budgeted_amount.currency,
            )
            for ind in result.baseline_indicators
        ]

        simulated_dtos = [
            CostCenterIndicatorDTO(
                cost_center_id=ind.cost_center_id,
                cost_center_code=ind.cost_center_code,
                period=str(ind.period),
                budgeted_amount=ind.budgeted_amount.amount,
                actual_amount=ind.actual_amount.amount,
                variance_amount=ind.variance_amount.amount,
                execution_rate=ind.execution_rate.value,
                status=ind.status.value,
                currency=ind.budgeted_amount.currency,
            )
            for ind in result.simulated_indicators
        ]

        impact_dtos = [
            CostCenterImpactDTO(
                cost_center_id=imp.cost_center_id,
                cost_center_code=imp.cost_center_code,
                baseline_actual=imp.baseline_actual.amount,
                simulated_actual=imp.simulated_actual.amount,
                delta_actual=imp.delta_actual.amount,
                baseline_status=imp.baseline_status.value,
                simulated_status=imp.simulated_status.value,
                new_overrun=imp.new_overrun,
                currency=imp.baseline_actual.currency,
            )
            for imp in result.impacts
        ]

        return SimulationResultDTO(
            scenario_name=result.scenario_name,
            period=str(result.period),
            baseline_indicators=baseline_dtos,
            simulated_indicators=simulated_dtos,
            impacts=impact_dtos,
        )

"""Use case for computing period indicators for cost centers."""

from decimal import Decimal

from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.indicators.application.dto import (
    ComputePeriodIndicatorsQuery,
    CostCenterIndicatorDTO,
    PeriodIndicatorsDTO,
)
from src.indicators.domain.services.variance_calculator import (
    BudgetVarianceCalculator,
)
from src.shared.domain.value_objects import Money, Percentage, Period


class ComputePeriodIndicatorsUseCase:
    """Orchestrates calculation of budget variance indicators for a period."""

    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        budget_repository: BudgetRepository,
        measurement_repository: MeasurementRepository,
    ) -> None:
        """Initialize use case with required repositories.

        Args:
            cost_center_repository: Repository for cost center lookups.
            budget_repository: Repository for planned budgets.
            measurement_repository: Repository for approved measurements.
        """
        self._cost_center_repository = cost_center_repository
        self._budget_repository = budget_repository
        self._measurement_repository = measurement_repository

    async def execute(self, query: ComputePeriodIndicatorsQuery) -> PeriodIndicatorsDTO:
        """Calculate period indicators across specified or all active cost centers.

        Args:
            query: Query specifying period and optional single cost center ID.

        Returns:
            PeriodIndicatorsDTO: Consolidated metrics for the period.
        """
        period = Period.from_string(query.period)

        if query.cost_center_id is not None:
            cc = await self._cost_center_repository.get_by_id(query.cost_center_id)
            cost_centers = [cc] if cc and cc.is_active else []
        else:
            cost_centers = await self._cost_center_repository.list_all(active_only=True)

        budgets = await self._budget_repository.list_by_period(period)
        measurements = await self._measurement_repository.list_by_period(period)

        indicator_dtos: list[CostCenterIndicatorDTO] = []
        total_budgeted_money = Money.zero("USD")
        total_actual_money = Money.zero("USD")

        for cc in cost_centers:
            ind = BudgetVarianceCalculator.calculate_from_records(
                cost_center_id=cc.id,
                cost_center_code=str(cc.code),
                period=period,
                budgets=budgets,
                measurements=measurements,
                currency="USD",
            )
            indicator_dtos.append(
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
            )
            total_budgeted_money += ind.budgeted_amount
            total_actual_money += ind.actual_amount

        total_variance_money = total_actual_money - total_budgeted_money
        if total_budgeted_money.amount > Decimal("0.00"):
            overall_rate = Percentage.from_ratio(
                total_actual_money.amount / total_budgeted_money.amount
            ).value
        else:
            overall_rate = Decimal("0.00")

        return PeriodIndicatorsDTO(
            period=str(period),
            indicators=indicator_dtos,
            total_budgeted=total_budgeted_money.amount,
            total_actual=total_actual_money.amount,
            total_variance=total_variance_money.amount,
            total_execution_rate=overall_rate,
            currency="USD",
        )

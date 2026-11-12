"""Use case for calculating direct and hierarchical budget totals."""

from decimal import Decimal

from src.budgeting.application.dto import (
    BudgetTargetDTO,
    GetHierarchyBudgetQuery,
    HierarchyBudgetDTO,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.shared.domain.value_objects import Money, Period


class GetHierarchyBudgetUseCase:
    """Computes direct and consolidated descendant budget targets for a cost center."""

    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        budget_repository: BudgetRepository,
    ) -> None:
        """Initialize use case with repositories.

        Args:
            cost_center_repository: Repository for cost center lookups.
            budget_repository: Repository for budget targets.
        """
        self._cost_center_repository = cost_center_repository
        self._budget_repository = budget_repository

    async def execute(self, query: GetHierarchyBudgetQuery) -> HierarchyBudgetDTO:
        """Calculate direct and consolidated hierarchical budget figures.

        Args:
            query: Query containing root cost center ID and period.

        Returns:
            HierarchyBudgetDTO: Consolidated budget metrics.
        """
        root = await self._cost_center_repository.get_by_id(query.cost_center_id)
        if root is None:
            raise CostCenterNotFoundError(
                f"Cost center {query.cost_center_id} not found."
            )

        period = Period.from_string(query.period)

        # 1. Direct budget lines
        direct_budgets = await self._budget_repository.get_by_cost_center_and_period(
            root.id, period
        )

        # 2. Descendant budget lines
        descendants = await self._cost_center_repository.get_descendants(root.id)
        all_budgets: list[BudgetTarget] = list(direct_budgets)

        for desc in descendants:
            desc_budgets = await self._budget_repository.get_by_cost_center_and_period(
                desc.id, period
            )
            all_budgets.extend(desc_budgets)

        currency = direct_budgets[0].amount.currency if direct_budgets else "USD"
        direct_sum = sum(
            (b.amount for b in direct_budgets),
            Money.zero(currency),
        )
        consolidated_sum = sum(
            (b.amount for b in all_budgets),
            Money.zero(currency),
        )

        budget_dtos = [
            BudgetTargetDTO(
                id=b.id,
                cost_center_id=b.cost_center_id,
                period=str(b.period),
                category=b.category,
                amount=b.amount.amount,
                currency=b.amount.currency,
            )
            for b in all_budgets
        ]

        return HierarchyBudgetDTO(
            cost_center_id=root.id,
            cost_center_code=str(root.code),
            period=str(period),
            direct_total=direct_sum.amount
            if isinstance(direct_sum, Money)
            else Decimal("0.00"),
            consolidated_total=consolidated_sum.amount
            if isinstance(consolidated_sum, Money)
            else Decimal("0.00"),
            currency=currency,
            budget_lines=budget_dtos,
        )

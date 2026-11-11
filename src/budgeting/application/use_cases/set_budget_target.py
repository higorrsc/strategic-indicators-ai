from decimal import Decimal

from src.budgeting.application.dto import (
    BudgetTargetDTO,
    SetBudgetTargetCommand,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.shared.domain.value_objects import Money, Period


class SetBudgetTargetUseCase:
    """Orchestrates establishing a planned budget line for a cost center in a period."""

    def __init__(
        self,
        cost_center_repository: CostCenterRepository,
        budget_repository: BudgetRepository,
    ) -> None:
        self._cost_center_repository = cost_center_repository
        self._budget_repository = budget_repository

    async def execute(self, command: SetBudgetTargetCommand) -> BudgetTargetDTO:
        cost_center = await self._cost_center_repository.get_by_id(
            command.cost_center_id
        )
        if cost_center is None:
            raise CostCenterNotFoundError(
                f"Cost center {command.cost_center_id} not found."
            )

        period = Period.from_string(command.period)
        money = Money(amount=Decimal(str(command.amount)), currency=command.currency)

        budget_target = BudgetTarget(
            cost_center_id=cost_center.id,
            period=period,
            category=command.category,
            amount=money,
        )
        await self._budget_repository.add(budget_target)

        return BudgetTargetDTO(
            id=budget_target.id,
            cost_center_id=budget_target.cost_center_id,
            period=str(budget_target.period),
            category=budget_target.category,
            amount=budget_target.amount.amount,
            currency=budget_target.amount.currency,
        )

from decimal import Decimal
from uuid import uuid4

import pytest

from src.budgeting.application.dto import (
    CreateCostCenterCommand,
    SetBudgetTargetCommand,
)
from src.budgeting.application.use_cases.commands import (
    CreateCostCenterUseCase,
    SetBudgetTargetUseCase,
)
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)


@pytest.mark.asyncio
async def test_should_set_budget_target_successfully() -> None:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()

    cc_use_case = CreateCostCenterUseCase(cc_repo)
    set_budget_use_case = SetBudgetTargetUseCase(cc_repo, budget_repo)

    cc = await cc_use_case.execute(CreateCostCenterCommand(code="1.0", name="Board"))

    result = await set_budget_use_case.execute(
        SetBudgetTargetCommand(
            cost_center_id=cc.id,
            period="2026-03",
            category="Executive Reserve",
            amount=Decimal("10000.00"),
        )
    )
    assert result.amount == Decimal("10000.00")
    assert result.category == "Executive Reserve"


@pytest.mark.asyncio
async def test_should_raise_when_cost_center_not_found() -> None:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    use_case = SetBudgetTargetUseCase(cc_repo, budget_repo)

    with pytest.raises(CostCenterNotFoundError):
        await use_case.execute(
            SetBudgetTargetCommand(
                cost_center_id=uuid4(),
                period="2026-03",
                category="Legal",
                amount=Decimal("1000.00"),
            )
        )

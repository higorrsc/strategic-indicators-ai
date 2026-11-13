from decimal import Decimal

import pytest

from src.budgeting.application.dto import (
    CreateCostCenterCommand,
    GetHierarchyBudgetQuery,
    SetBudgetTargetCommand,
)
from src.budgeting.application.use_cases.commands import (
    CreateCostCenterUseCase,
    SetBudgetTargetUseCase,
)
from src.budgeting.application.use_cases.queries import (
    GetHierarchyBudgetUseCase,
)
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)


@pytest.mark.asyncio
async def test_should_create_hierarchy_and_aggregate_budget() -> None:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()

    create_cc_use_case = CreateCostCenterUseCase(cc_repo)
    set_budget_use_case = SetBudgetTargetUseCase(cc_repo, budget_repo)
    get_hierarchy_use_case = GetHierarchyBudgetUseCase(cc_repo, budget_repo)

    # 1. Create root 1.0
    root_dto = await create_cc_use_case.execute(
        CreateCostCenterCommand(code="1.0", name="Executive Board")
    )
    # 2. Create child 1.1
    child_dto = await create_cc_use_case.execute(
        CreateCostCenterCommand(
            code="1.1",
            name="Technology",
            parent_id=root_dto.id,
        )
    )
    # 3. Create sub-child 1.1.1
    subchild_dto = await create_cc_use_case.execute(
        CreateCostCenterCommand(
            code="1.1.1",
            name="DevOps & Cloud",
            parent_id=child_dto.id,
        )
    )

    # Set budget lines
    await set_budget_use_case.execute(
        SetBudgetTargetCommand(
            cost_center_id=root_dto.id,
            period="2026-03",
            category="Executive Reserve",
            amount=Decimal("10000.00"),
        )
    )
    await set_budget_use_case.execute(
        SetBudgetTargetCommand(
            cost_center_id=child_dto.id,
            period="2026-03",
            category="Tech Operations",
            amount=Decimal("20000.00"),
        )
    )
    await set_budget_use_case.execute(
        SetBudgetTargetCommand(
            cost_center_id=subchild_dto.id,
            period="2026-03",
            category="Cloud Hosting",
            amount=Decimal("30000.00"),
        )
    )

    # Query hierarchy for root 1.0
    hierarchy = await get_hierarchy_use_case.execute(
        GetHierarchyBudgetQuery(
            cost_center_id=root_dto.id,
            period="2026-03",
        )
    )

    assert hierarchy.direct_total == Decimal("10000.00")
    assert hierarchy.consolidated_total == Decimal("60000.00")
    assert len(hierarchy.budget_lines) == 3

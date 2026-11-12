from decimal import Decimal
from uuid import uuid4

import pytest

from src.budgeting.application.dto import (
    CreateCostCenterCommand,
    GetHierarchyBudgetQuery,
    SetBudgetTargetCommand,
)
from src.budgeting.application.use_cases import (
    CreateCostCenterUseCase,
    GetHierarchyBudgetUseCase,
    SetBudgetTargetUseCase,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.exceptions import (
    CircularCostCenterHierarchyError,
    CostCenterNotFoundError,
    DuplicateCostCenterCodeError,
    InvalidBudgetTargetError,
)
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode, Money, Period


class TestCostCenterEntity:
    def test_should_create_cost_center(self) -> None:
        cc = CostCenter(code=CostCenterCode("1.0"), name="Executive Board")
        assert cc.name == "Executive Board"
        assert cc.is_active is True
        assert cc.parent_id is None

    def test_should_reject_empty_name(self) -> None:
        with pytest.raises(InvalidBudgetTargetError):
            CostCenter(code=CostCenterCode("1.0"), name="   ")

    def test_should_prevent_self_parenting(self) -> None:
        same_id = uuid4()
        with pytest.raises(CircularCostCenterHierarchyError):
            CostCenter(
                id=same_id,
                code=CostCenterCode("1.0"),
                name="Board",
                parent_id=same_id,
            )

    def test_should_activate_and_deactivate(self) -> None:
        cc = CostCenter(code=CostCenterCode("1.0"), name="Board")
        cc.deactivate()
        assert not cc.is_active
        cc.activate()
        assert cc.is_active


class TestBudgetTargetEntity:
    def test_should_create_valid_budget_target(self) -> None:
        cc_id = uuid4()
        period = Period.from_string("2026-03")
        target = BudgetTarget(
            cost_center_id=cc_id,
            period=period,
            category="Cloud Infrastructure",
            amount=Money.from_float_or_int(50000, "USD"),
        )
        assert target.amount.amount == Decimal("50000.00")

    def test_should_reject_negative_budget_target(self) -> None:
        cc_id = uuid4()
        period = Period.from_string("2026-03")
        with pytest.raises(InvalidBudgetTargetError):
            BudgetTarget(
                cost_center_id=cc_id,
                period=period,
                category="Hardware",
                amount=Money(Decimal("-10.00"), "USD"),
            )


@pytest.mark.asyncio
class TestBudgetingUseCases:
    async def test_should_create_hierarchy_and_aggregate_budget(self) -> None:
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

    async def test_should_reject_duplicate_code(self) -> None:
        cc_repo = InMemoryCostCenterRepository()
        use_case = CreateCostCenterUseCase(cc_repo)

        await use_case.execute(CreateCostCenterCommand(code="1.0", name="Board A"))
        with pytest.raises(DuplicateCostCenterCodeError):
            await use_case.execute(CreateCostCenterCommand(code="1.0", name="Board B"))

    async def test_should_raise_when_cost_center_not_found(self) -> None:
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

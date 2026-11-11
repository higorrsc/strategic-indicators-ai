from __future__ import annotations

from uuid import UUID

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.exceptions import (
    CircularCostCenterHierarchyError,
    CostCenterNotFoundError,
    DuplicateCostCenterCodeError,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode, Period


class InMemoryCostCenterRepository(CostCenterRepository):
    """In-memory test double implementation for CostCenterRepository."""

    def __init__(self) -> None:
        self._cost_centers: dict[UUID, CostCenter] = {}

    async def add(self, cost_center: CostCenter) -> None:
        for existing in self._cost_centers.values():
            if existing.code == cost_center.code:
                raise DuplicateCostCenterCodeError(
                    f"Cost center code '{cost_center.code}' already exists."
                )
        if (
            cost_center.parent_id is not None
            and cost_center.parent_id not in self._cost_centers
        ):
            raise CostCenterNotFoundError(
                f"Parent cost center ID {cost_center.parent_id} does not exist."
            )
        self._cost_centers[cost_center.id] = cost_center

    async def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        return self._cost_centers.get(cost_center_id)

    async def get_by_code(self, code: CostCenterCode) -> CostCenter | None:
        for cc in self._cost_centers.values():
            if cc.code == code:
                return cc
        return None

    async def get_children(self, parent_id: UUID) -> list[CostCenter]:
        return [
            cc
            for cc in self._cost_centers.values()
            if cc.parent_id == parent_id and cc.is_active
        ]

    async def get_descendants(self, root_id: UUID) -> list[CostCenter]:
        descendants: list[CostCenter] = []
        visited: set[UUID] = {root_id}

        queue = await self.get_children(root_id)
        while queue:
            current = queue.pop(0)
            if current.id in visited:
                raise CircularCostCenterHierarchyError(
                    f"Circular hierarchy cycle detected at node {current.id}."
                )
            visited.add(current.id)
            descendants.append(current)
            children = await self.get_children(current.id)
            queue.extend(children)

        return descendants

    async def list_all(self, active_only: bool = True) -> list[CostCenter]:
        if active_only:
            return [cc for cc in self._cost_centers.values() if cc.is_active]
        return list(self._cost_centers.values())

    async def update(self, cost_center: CostCenter) -> None:
        if cost_center.id not in self._cost_centers:
            raise CostCenterNotFoundError(
                f"Cost center ID {cost_center.id} does not exist."
            )
        # Check if new parent creates cycle
        if cost_center.parent_id is not None:
            descendants = await self.get_descendants(cost_center.id)
            descendant_ids = {d.id for d in descendants}
            if cost_center.parent_id in descendant_ids:
                raise CircularCostCenterHierarchyError(
                    "Cannot assign descendant as parent cost center."
                )
        self._cost_centers[cost_center.id] = cost_center


class InMemoryBudgetRepository(BudgetRepository):
    """In-memory test double implementation for BudgetRepository."""

    def __init__(self) -> None:
        self._budgets: dict[UUID, BudgetTarget] = {}

    async def add(self, budget_target: BudgetTarget) -> None:
        self._budgets[budget_target.id] = budget_target

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        return self._budgets.get(budget_id)

    async def get_by_cost_center_and_period(
        self, cost_center_id: UUID, period: Period
    ) -> list[BudgetTarget]:
        return [
            b
            for b in self._budgets.values()
            if b.cost_center_id == cost_center_id and b.period == period
        ]

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        return [b for b in self._budgets.values() if b.period == period]

    async def update(self, budget_target: BudgetTarget) -> None:
        self._budgets[budget_target.id] = budget_target

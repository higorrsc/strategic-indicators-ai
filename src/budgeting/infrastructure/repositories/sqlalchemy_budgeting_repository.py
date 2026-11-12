"""SQLAlchemy repository implementations for Budgeting Bounded Context."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.budgeting.infrastructure.database.models import (
    BudgetTargetModel,
    CostCenterModel,
)
from src.shared.domain.value_objects import CostCenterCode, Money, Period


def _to_cost_center_entity(model: CostCenterModel) -> CostCenter:
    """Map a CostCenterModel to a pure CostCenter domain entity."""
    return CostCenter(
        id=model.id,
        code=CostCenterCode(model.code),
        name=model.name,
        parent_id=model.parent_id,
        is_active=model.is_active,
    )


def _to_budget_target_entity(model: BudgetTargetModel) -> BudgetTarget:
    """Map a BudgetTargetModel to a pure BudgetTarget domain entity."""
    return BudgetTarget(
        id=model.id,
        cost_center_id=model.cost_center_id,
        period=Period.from_string(model.period),
        category=model.category,
        amount=Money(model.amount, model.currency),
    )


class SqlAlchemyCostCenterRepository(CostCenterRepository):
    """SQLAlchemy implementation of CostCenterRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session: The active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def add(self, cost_center: CostCenter) -> None:
        """Persist a new cost center.

        Args:
            cost_center: Cost center entity to persist.
        """
        model = CostCenterModel(
            id=cost_center.id,
            code=cost_center.code.value,
            name=cost_center.name,
            parent_id=cost_center.parent_id,
            is_active=cost_center.is_active,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        """Find cost center by unique identifier.

        Args:
            cost_center_id: Cost center UUID.

        Returns:
            CostCenter if found, None otherwise.
        """
        stmt = select(CostCenterModel).where(CostCenterModel.id == cost_center_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_cost_center_entity(model) if model else None

    async def get_by_code(self, code: CostCenterCode) -> CostCenter | None:
        """Find cost center by hierarchical code.

        Args:
            code: Cost center code.

        Returns:
            CostCenter if found, None otherwise.
        """
        stmt = select(CostCenterModel).where(CostCenterModel.code == code.value)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_cost_center_entity(model) if model else None

    async def get_children(self, parent_id: UUID) -> list[CostCenter]:
        """List direct child cost centers.

        Args:
            parent_id: Parent cost center UUID.

        Returns:
            List of active child cost centers.
        """
        stmt = select(CostCenterModel).where(
            CostCenterModel.parent_id == parent_id,
            CostCenterModel.is_active.is_(True),
        )
        result = await self._session.execute(stmt)
        return [_to_cost_center_entity(m) for m in result.scalars().all()]

    async def get_descendants(self, root_id: UUID) -> list[CostCenter]:
        """List all descendant cost centers in hierarchy.

        Args:
            root_id: Root cost center UUID.

        Returns:
            List of all descendant cost centers.
        """
        all_centers = await self.list_all(active_only=True)
        children_map: dict[UUID, list[CostCenter]] = {}
        for center in all_centers:
            if center.parent_id is not None:
                children_map.setdefault(center.parent_id, []).append(center)

        descendants: list[CostCenter] = []
        queue = list(children_map.get(root_id, []))
        while queue:
            current = queue.pop(0)
            descendants.append(current)
            queue.extend(children_map.get(current.id, []))
        return descendants

    async def list_all(self, active_only: bool = True) -> list[CostCenter]:
        """List all cost centers in system.

        Args:
            active_only: Whether to include active nodes only.

        Returns:
            List of cost centers.
        """
        stmt = select(CostCenterModel)
        if active_only:
            stmt = stmt.where(CostCenterModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [_to_cost_center_entity(m) for m in result.scalars().all()]

    async def update(self, cost_center: CostCenter) -> None:
        """Update existing cost center.

        Args:
            cost_center: Modified cost center entity.
        """
        stmt = select(CostCenterModel).where(CostCenterModel.id == cost_center.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.code = cost_center.code.value
            model.name = cost_center.name
            model.parent_id = cost_center.parent_id
            model.is_active = cost_center.is_active
            await self._session.flush()


class SqlAlchemyBudgetRepository(BudgetRepository):
    """SQLAlchemy implementation of BudgetRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session: The active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def add(self, budget_target: BudgetTarget) -> None:
        """Persist a new budget target.

        Args:
            budget_target: The budget target entity to store.
        """
        model = BudgetTargetModel(
            id=budget_target.id,
            cost_center_id=budget_target.cost_center_id,
            period=budget_target.period.value,
            category=budget_target.category,
            amount=budget_target.amount.amount,
            currency=budget_target.amount.currency,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        """Find budget target by identifier.

        Args:
            budget_id: Target UUID.

        Returns:
            BudgetTarget if found, None otherwise.
        """
        stmt = select(BudgetTargetModel).where(BudgetTargetModel.id == budget_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_budget_target_entity(model) if model else None

    async def get_by_cost_center_and_period(
        self, cost_center_id: UUID, period: Period
    ) -> list[BudgetTarget]:
        """Find all budget target lines for cost center in period.

        Args:
            cost_center_id: Cost center UUID.
            period: Target period.

        Returns:
            List of matching budget targets.
        """
        stmt = select(BudgetTargetModel).where(
            BudgetTargetModel.cost_center_id == cost_center_id,
            BudgetTargetModel.period == period.value,
        )
        result = await self._session.execute(stmt)
        return [_to_budget_target_entity(m) for m in result.scalars().all()]

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        """Find all budget targets across all cost centers in period.

        Args:
            period: Target fiscal period.

        Returns:
            List of budget targets.
        """
        stmt = select(BudgetTargetModel).where(BudgetTargetModel.period == period.value)
        result = await self._session.execute(stmt)
        return [_to_budget_target_entity(m) for m in result.scalars().all()]

    async def update(self, budget_target: BudgetTarget) -> None:
        """Update existing budget target.

        Args:
            budget_target: The modified budget target entity.
        """
        stmt = select(BudgetTargetModel).where(BudgetTargetModel.id == budget_target.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is not None:
            model.category = budget_target.category
            model.amount = budget_target.amount.amount
            model.currency = budget_target.amount.currency
            await self._session.flush()

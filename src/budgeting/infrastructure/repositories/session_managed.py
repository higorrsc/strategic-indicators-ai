"""Session-managed budgeting repository wrappers."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode, Period

from .sqlalchemy_budgeting_repository import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyCostCenterRepository,
)


class SessionManagedCostCenterRepository(CostCenterRepository):
    """CostCenterRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, cost_center: CostCenter) -> None:
        """Persist cost center and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            await repo.add(cost_center)
            await session.commit()

    async def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        """Find cost center by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_by_id(cost_center_id)

    async def get_by_code(self, code: CostCenterCode) -> CostCenter | None:
        """Find cost center by code."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_by_code(code)

    async def get_children(self, parent_id: UUID) -> list[CostCenter]:
        """List active children."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_children(parent_id)

    async def get_descendants(self, root_id: UUID) -> list[CostCenter]:
        """List all descendants."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_descendants(root_id)

    async def list_all(self, active_only: bool = True) -> list[CostCenter]:
        """List all cost centers."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.list_all(active_only=active_only)

    async def update(self, cost_center: CostCenter) -> None:
        """Update cost center and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            await repo.update(cost_center)
            await session.commit()


class SessionManagedBudgetRepository(BudgetRepository):
    """BudgetRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, budget_target: BudgetTarget) -> None:
        """Persist budget target and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            await repo.add(budget_target)
            await session.commit()

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        """Find budget target by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.get_by_id(budget_id)

    async def get_by_cost_center_and_period(
        self, cost_center_id: UUID, period: Period
    ) -> list[BudgetTarget]:
        """Find targets by cost center and period."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.get_by_cost_center_and_period(cost_center_id, period)

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        """List targets across all centers in period."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.list_by_period(period)

    async def update(self, budget_target: BudgetTarget) -> None:
        """Update budget target and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            await repo.update(budget_target)
            await session.commit()

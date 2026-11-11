"""Repository interface for Budget persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.shared.domain.value_objects import Period


class BudgetRepository(Protocol):
    """Repository abstraction for Planned Budget persistence."""

    async def add(self, budget_target: BudgetTarget) -> None:
        """Persist a new budget target.

        Args:
            budget_target: The budget target entity to store.
        """
        ...

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        """Find budget target by identifier.

        Args:
            budget_id: Target UUID.

        Returns:
            BudgetTarget if found, None otherwise.
        """
        ...

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
        ...

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        """Find all budget targets across all cost centers in period.

        Args:
            period: Target fiscal period.

        Returns:
            List of budget targets.
        """
        ...

    async def update(self, budget_target: BudgetTarget) -> None:
        """Update existing budget target.

        Args:
            budget_target: The modified budget target entity.
        """
        ...

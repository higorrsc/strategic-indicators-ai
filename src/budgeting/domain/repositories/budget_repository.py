from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.shared.domain.value_objects import Period


class BudgetRepository(Protocol):
    """Repository abstraction for Planned Budget persistence."""

    async def add(self, budget_target: BudgetTarget) -> None:
        """Persist a new budget target."""
        ...

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        """Find budget target by identifier."""
        ...

    async def get_by_cost_center_and_period(
        self, cost_center_id: UUID, period: Period
    ) -> list[BudgetTarget]:
        """Find all budget target lines for cost center in period."""
        ...

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        """Find all budget targets across all cost centers in period."""
        ...

    async def update(self, budget_target: BudgetTarget) -> None:
        """Update existing budget target."""
        ...

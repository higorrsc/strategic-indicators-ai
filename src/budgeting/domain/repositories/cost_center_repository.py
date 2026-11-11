from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.budgeting.domain.entities.cost_center import CostCenter
from src.shared.domain.value_objects import CostCenterCode


class CostCenterRepository(Protocol):
    """Repository abstraction for Cost Center persistence."""

    async def add(self, cost_center: CostCenter) -> None:
        """Persist a new cost center."""
        ...

    async def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        """Find cost center by unique identifier."""
        ...

    async def get_by_code(self, code: CostCenterCode) -> CostCenter | None:
        """Find cost center by hierarchical code."""
        ...

    async def get_children(self, parent_id: UUID) -> list[CostCenter]:
        """List direct child cost centers."""
        ...

    async def get_descendants(self, root_id: UUID) -> list[CostCenter]:
        """List all descendant cost centers in hierarchy."""
        ...

    async def list_all(self, active_only: bool = True) -> list[CostCenter]:
        """List all cost centers in system."""
        ...

    async def update(self, cost_center: CostCenter) -> None:
        """Update existing cost center."""
        ...

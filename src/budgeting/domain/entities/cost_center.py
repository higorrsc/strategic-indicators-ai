from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.budgeting.domain.exceptions import (
    CircularCostCenterHierarchyError,
    InvalidBudgetTargetError,
)
from src.shared.domain.value_objects import CostCenterCode


@dataclass(slots=True)
class CostCenter:
    """Cost Center aggregate entity representing an organizational budgeting unit."""

    code: CostCenterCode
    name: str
    id: UUID = field(default_factory=uuid4)
    parent_id: UUID | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        trimmed_name = self.name.strip()
        if not trimmed_name:
            raise InvalidBudgetTargetError("Cost center name cannot be empty.")
        self.name = trimmed_name
        if self.parent_id is not None and self.parent_id == self.id:
            raise CircularCostCenterHierarchyError(
                "Cost center cannot be its own parent."
            )

    def deactivate(self) -> None:
        """Deactivate cost center."""
        self.is_active = False

    def activate(self) -> None:
        """Activate cost center."""
        self.is_active = True

    def reassign_parent(self, new_parent_id: UUID | None) -> None:
        """Reassign parent cost center preventing self-reference."""
        if new_parent_id is not None and new_parent_id == self.id:
            raise CircularCostCenterHierarchyError(
                "Cost center cannot be its own parent."
            )
        self.parent_id = new_parent_id

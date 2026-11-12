"""Contract entity and allocation share definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4

from src.allocation.domain.exceptions import (
    AllocationDomainError,
    InvalidAllocationPercentageError,
)
from src.shared.domain.value_objects import Percentage


@dataclass(frozen=True, slots=True)
class AllocationShare:
    """Represents a planned percentage share assigned to a cost center."""

    cost_center_id: UUID
    percentage: Percentage


@dataclass(slots=True)
class Contract:
    """Contract entity representing an active agreement with a supplier."""

    code: str
    supplier_id: UUID
    title: str
    id: UUID = field(default_factory=uuid4)
    default_allocations: list[AllocationShare] = field(default_factory=list)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate contract code, title, and initial allocation percentages."""
        trimmed_code = self.code.strip()
        trimmed_title = self.title.strip()
        if not trimmed_code:
            raise AllocationDomainError("Contract code cannot be empty.")
        if not trimmed_title:
            raise AllocationDomainError("Contract title cannot be empty.")
        self.code = trimmed_code
        self.title = trimmed_title

        if self.default_allocations:
            self._validate_allocations_sum(self.default_allocations)

    @staticmethod
    def _validate_allocations_sum(allocations: list[AllocationShare]) -> None:
        """Validate that total percentage allocation equals 100.00%.

        Args:
            allocations: List of allocation shares to validate.

        Raises:
            InvalidAllocationPercentageError: If total does not equal 100.00%.
        """
        total = sum((share.percentage.value for share in allocations), Decimal("0.00"))
        if total != Decimal("100.00"):
            raise InvalidAllocationPercentageError(
                f"Allocation shares must sum to 100.00%, got {total}%."
            )

    def set_default_allocations(self, allocations: list[AllocationShare]) -> None:
        """Update default allocation template ensuring 100% distribution invariant.

        Args:
            allocations: List of allocation shares.
        """
        if allocations:
            self._validate_allocations_sum(allocations)
        self.default_allocations = list(allocations)

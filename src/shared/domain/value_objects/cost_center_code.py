"""Hierarchical cost center code value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.exceptions import InvalidCostCenterCodeError

_CODE_REGEX = re.compile(r"^[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class CostCenterCode:
    """Immutable Value Object for hierarchical cost center codes (e.g. 1.0, 1.1)."""

    value: str

    def __post_init__(self) -> None:
        """Validate hierarchical cost center code format."""
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidCostCenterCodeError("Cost center code cannot be empty.")
        if not _CODE_REGEX.match(trimmed):
            raise InvalidCostCenterCodeError(
                f"Cost center code '{trimmed}' has invalid hierarchical syntax."
            )
        object.__setattr__(self, "value", trimmed)

    @property
    def segments(self) -> list[str]:
        """Return dot-separated code segments."""
        return self.value.split(".")

    @property
    def level(self) -> int:
        """Hierarchy depth level starting at 1 for root codes."""
        return len(self.segments)

    @property
    def parent_code(self) -> CostCenterCode | None:
        """Return parent CostCenterCode or None if this is a root node."""
        parts = self.segments
        if len(parts) <= 1:
            return None
        return CostCenterCode(".".join(parts[:-1]))

    def is_ancestor_of(self, other: CostCenterCode) -> bool:
        """Check if self is an ancestor of other code in hierarchy.

        Args:
            other: The candidate descendant code.

        Returns:
            True if self is an ancestor of other.
        """
        return other.value.startswith(f"{self.value}.") and other.level > self.level

    def is_descendant_of(self, other: CostCenterCode) -> bool:
        """Check if self is a descendant of other code in hierarchy.

        Args:
            other: The candidate ancestor code.

        Returns:
            True if self is a descendant of other.
        """
        return other.is_ancestor_of(self)

    def __str__(self) -> str:
        """Return string value."""
        return self.value

    def __repr__(self) -> str:
        """Return developer representation."""
        return f"CostCenterCode('{self.value}')"

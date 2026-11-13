"""Hierarchical accounting account code value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.exceptions import InvalidAccountCodeError

_CODE_REGEX = re.compile(r"^\d+(\.\d+)*$")


@dataclass(frozen=True, slots=True)
class AccountCode:
    """Immutable Value Object for accounting account codes (e.g. 3.1.01)."""

    value: str

    def __post_init__(self) -> None:
        """Validate hierarchical accounting account code format."""
        trimmed = self.value.strip()
        if not trimmed:
            raise InvalidAccountCodeError("Accounting account code cannot be empty.")
        if not _CODE_REGEX.match(trimmed):
            raise InvalidAccountCodeError(
                f"Accounting account code '{trimmed}' has invalid hierarchical syntax."
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
    def parent_code(self) -> AccountCode | None:
        """Return parent AccountCode or None if this is a root node."""
        parts = self.segments
        if len(parts) <= 1:
            return None
        return AccountCode(".".join(parts[:-1]))

    def is_ancestor_of(self, other: AccountCode) -> bool:
        """Check if self is an ancestor of other code in hierarchy.

        Args:
            other: The candidate descendant code.

        Returns:
            True if self is an ancestor of other.
        """
        return other.value.startswith(f"{self.value}.") and other.level > self.level

    def is_descendant_of(self, other: AccountCode) -> bool:
        """Check if self is a descendant of other code in hierarchy.

        Args:
            other: The candidate ancestor code.

        Returns:
            True if self is a descendant of other.
        """
        return other.is_ancestor_of(self)

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

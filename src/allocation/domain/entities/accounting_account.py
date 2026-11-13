"""Accounting account domain entity representing chart of accounts."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.allocation.domain.exceptions import AllocationDomainError
from src.shared.domain.value_objects import AccountCode


@dataclass(slots=True)
class AccountingAccount:
    """Accounting account entity representing a budgetary and financial ledger code."""

    code: AccountCode
    name: str
    description: str = ""
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True

    def __post_init__(self) -> None:
        """Validate account name."""
        trimmed_name = self.name.strip()
        if not trimmed_name:
            raise AllocationDomainError("Accounting account name cannot be empty.")
        self.name = trimmed_name
        self.description = self.description.strip()

    def deactivate(self) -> None:
        """Deactivate account preventing future allocations."""
        self.is_active = False

    def activate(self) -> None:
        """Reactivate account allowing future allocations."""
        self.is_active = True

    def update_details(self, name: str, description: str) -> None:
        """Update account name and description.

        Args:
            name: New account name.
            description: New description.
        """
        trimmed = name.strip()
        if not trimmed:
            raise AllocationDomainError("Accounting account name cannot be empty.")
        self.name = trimmed
        self.description = description.strip()

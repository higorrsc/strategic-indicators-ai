"""Repository port for accounting account entities."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.shared.domain.value_objects import AccountCode


class AccountingAccountRepository(Protocol):
    """Port interface for storing and retrieving accounting accounts."""

    async def save(self, account: AccountingAccount) -> None:
        """Persist a new or modified accounting account.

        Args:
            account: Accounting account entity to save.
        """
        ...

    async def get_by_id(self, account_id: UUID) -> AccountingAccount | None:
        """Retrieve accounting account by identifier.

        Args:
            account_id: Unique account UUID.

        Returns:
            AccountingAccount or None if not found.
        """
        ...

    async def get_by_code(self, code: AccountCode) -> AccountingAccount | None:
        """Retrieve accounting account by hierarchical code.

        Args:
            code: AccountCode value object.

        Returns:
            AccountingAccount or None if not found.
        """
        ...

    async def list_all(
        self,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AccountingAccount]:
        """List accounting accounts with optional active filter and pagination.

        Args:
            active_only: Whether to restrict to active accounts.
            offset: Number of items to skip.
            limit: Maximum items to return.

        Returns:
            List of accounting accounts.
        """
        ...

    async def count(self, active_only: bool = True) -> int:
        """Count total accounting accounts.

        Args:
            active_only: Whether to count only active accounts.

        Returns:
            Total count.
        """
        ...

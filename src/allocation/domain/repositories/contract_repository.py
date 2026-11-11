"""Repository interface for Contract persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.contract import Contract


class ContractRepository(Protocol):
    """Repository abstraction for Contract persistence."""

    async def add(self, contract: Contract) -> None:
        """Persist a new contract.

        Args:
            contract: Contract entity to add.
        """
        ...

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        """Find contract by identifier.

        Args:
            contract_id: Contract UUID.

        Returns:
            Contract if found, None otherwise.
        """
        ...

    async def get_by_code(self, code: str) -> Contract | None:
        """Find contract by alphanumeric code.

        Args:
            code: Contract code.

        Returns:
            Contract if found, None otherwise.
        """
        ...

    async def list_all(self, active_only: bool = True) -> list[Contract]:
        """List all contracts.

        Args:
            active_only: Whether to filter active contracts only.

        Returns:
            List of contracts.
        """
        ...

    async def update(self, contract: Contract) -> None:
        """Update existing contract.

        Args:
            contract: Modified contract entity.
        """
        ...

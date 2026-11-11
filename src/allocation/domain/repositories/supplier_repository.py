"""Repository interface for Supplier persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.supplier import Supplier


class SupplierRepository(Protocol):
    """Repository abstraction for Supplier persistence."""

    async def add(self, supplier: Supplier) -> None:
        """Persist a new supplier.

        Args:
            supplier: Supplier entity to add.
        """
        ...

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        """Find supplier by identifier.

        Args:
            supplier_id: Supplier UUID.

        Returns:
            Supplier if found, None otherwise.
        """
        ...

    async def list_all(self) -> list[Supplier]:
        """List all suppliers.

        Returns:
            List of suppliers.
        """
        ...

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.supplier import Supplier


class SupplierRepository(Protocol):
    """Repository abstraction for Supplier persistence."""

    async def add(self, supplier: Supplier) -> None: ...

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None: ...

    async def list_all(self) -> list[Supplier]: ...

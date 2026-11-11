from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.contract import Contract


class ContractRepository(Protocol):
    """Repository abstraction for Contract persistence."""

    async def add(self, contract: Contract) -> None: ...

    async def get_by_id(self, contract_id: UUID) -> Contract | None: ...

    async def get_by_code(self, code: str) -> Contract | None: ...

    async def list_all(self, active_only: bool = True) -> list[Contract]: ...

    async def update(self, contract: Contract) -> None: ...

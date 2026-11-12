"""Use case for querying and listing vendor contracts."""

from __future__ import annotations

from src.allocation.application.dto import (
    AllocationShareDTO,
    ContractDTO,
    ListContractsQuery,
)
from src.allocation.domain.repositories.contract_repository import (
    ContractRepository,
)


class ListContractsUseCase:
    """Orchestrates contract querying with optional filtering."""

    def __init__(self, contract_repository: ContractRepository) -> None:
        """Initialize use case with contract repository.

        Args:
            contract_repository: Repository for contract persistence.
        """
        self._contract_repository = contract_repository

    async def execute(
        self, query: ListContractsQuery | None = None
    ) -> list[ContractDTO]:
        """Query contracts matching filter criteria.

        Args:
            query: Optional filter parameters.

        Returns:
            list[ContractDTO]: List of matching contracts.
        """
        q = query or ListContractsQuery()
        contracts = await self._contract_repository.list_all(active_only=q.active_only)
        if q.supplier_id is not None:
            contracts = [c for c in contracts if c.supplier_id == q.supplier_id]

        return [
            ContractDTO(
                id=c.id,
                code=c.code,
                supplier_id=c.supplier_id,
                title=c.title,
                default_allocations=[
                    AllocationShareDTO(
                        cost_center_id=a.cost_center_id,
                        percentage=a.percentage.value,
                    )
                    for a in c.default_allocations
                ],
                is_active=c.is_active,
            )
            for c in contracts
        ]

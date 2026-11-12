"""Use case for querying and listing vendor contracts."""

from __future__ import annotations

from src.allocation.application.dto import (
    AllocationShareDTO,
    ContractDTO,
    ListContractsQuery,
    PaginatedResultDTO,
)
from src.allocation.domain.repositories.contract_repository import (
    ContractRepository,
)


class ListContractsUseCase:
    """Orchestrates contract querying with optional filtering and pagination."""

    def __init__(self, contract_repository: ContractRepository) -> None:
        """Initialize use case with contract repository.

        Args:
            contract_repository: Repository for contract persistence.
        """
        self._contract_repository = contract_repository

    async def execute(
        self, query: ListContractsQuery | None = None
    ) -> PaginatedResultDTO[ContractDTO]:
        """Query contracts matching filter criteria and pagination.

        Args:
            query: Optional filter and pagination parameters.

        Returns:
            PaginatedResultDTO[ContractDTO]: Paginated contracts result.
        """
        q = query or ListContractsQuery()
        contracts = await self._contract_repository.list_all(active_only=q.active_only)
        if q.supplier_id is not None:
            contracts = [c for c in contracts if c.supplier_id == q.supplier_id]

        total_items = len(contracts)
        offset = (q.page - 1) * q.per_page
        sliced = contracts[offset : offset + q.per_page]

        dtos = [
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
            for c in sliced
        ]
        return PaginatedResultDTO(
            items=dtos,
            total_items=total_items,
            page=q.page,
            per_page=q.per_page,
        )

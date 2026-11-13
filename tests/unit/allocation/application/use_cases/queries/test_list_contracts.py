from uuid import uuid4

import pytest

from src.allocation.application.dto import ListContractsQuery
from src.allocation.application.use_cases.queries import ListContractsUseCase
from src.allocation.domain.entities.contract import Contract
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
)


@pytest.mark.asyncio
async def test_should_list_contracts_with_filters() -> None:
    repo = InMemoryContractRepository()
    sup1, sup2 = uuid4(), uuid4()

    c1 = Contract(code="CT-01", supplier_id=sup1, title="Active Sup1", is_active=True)
    c2 = Contract(
        code="CT-02", supplier_id=sup1, title="Inactive Sup1", is_active=False
    )
    c3 = Contract(code="CT-03", supplier_id=sup2, title="Active Sup2", is_active=True)
    await repo.add(c1)
    await repo.add(c2)
    await repo.add(c3)

    use_case = ListContractsUseCase(repo)

    # Default: active only
    active = await use_case.execute()
    assert len(active.items) == 2
    assert active.total_items == 2
    assert active.page == 1
    assert active.per_page == 20

    # All contracts
    all_contracts = await use_case.execute(ListContractsQuery(active_only=False))
    assert len(all_contracts.items) == 3
    assert all_contracts.total_items == 3

    # Filter by supplier
    sup1_active = await use_case.execute(
        ListContractsQuery(supplier_id=sup1, active_only=True)
    )
    assert len(sup1_active.items) == 1
    assert sup1_active.items[0].code == "CT-01"

    # Pagination slicing
    paginated = await use_case.execute(
        ListContractsQuery(active_only=False, page=1, per_page=2)
    )
    assert len(paginated.items) == 2
    assert paginated.total_items == 3
    assert paginated.page == 1
    assert paginated.per_page == 2

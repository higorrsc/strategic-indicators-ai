from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import AllocationShareDTO, RegisterContractCommand
from src.allocation.application.use_cases.commands import RegisterContractUseCase
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
    InMemorySupplierRepository,
)


@pytest.mark.asyncio
async def test_should_register_contract_successfully() -> None:
    sup_repo = InMemorySupplierRepository()
    contract_repo = InMemoryContractRepository()

    supplier = Supplier(name="Cloud Corp", tax_id="12.345.678/0001-90")
    await sup_repo.add(supplier)

    cc1, cc2 = uuid4(), uuid4()

    use_case = RegisterContractUseCase(contract_repo, sup_repo)
    contract_dto = await use_case.execute(
        RegisterContractCommand(
            code="CT-2026-01",
            supplier_id=supplier.id,
            title="Cloud Infrastructure",
            default_allocations=[
                AllocationShareDTO(cost_center_id=cc1, percentage=Decimal("80.00")),
                AllocationShareDTO(cost_center_id=cc2, percentage=Decimal("20.00")),
            ],
        )
    )
    assert contract_dto.code == "CT-2026-01"
    assert contract_dto.supplier_id == supplier.id
    assert len(contract_dto.default_allocations) == 2

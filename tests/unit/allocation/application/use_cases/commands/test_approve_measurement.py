from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import (
    AllocationShareDTO,
    ApproveMeasurementCommand,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.application.use_cases.commands import (
    ApproveMeasurementUseCase,
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
)


@pytest.mark.asyncio
async def test_should_approve_measurement() -> None:
    sup_repo = InMemorySupplierRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()

    supplier = Supplier(name="Cloud Corp", tax_id="12.345.678/0001-90")
    await sup_repo.add(supplier)

    cc1 = uuid4()

    reg_contract_use_case = RegisterContractUseCase(contract_repo, sup_repo)
    contract_dto = await reg_contract_use_case.execute(
        RegisterContractCommand(
            code="CT-2026-01",
            supplier_id=supplier.id,
            title="Cloud Infrastructure",
            default_allocations=[
                AllocationShareDTO(cost_center_id=cc1, percentage=Decimal("100.00")),
            ],
        )
    )

    submit_use_case = SubmitMeasurementUseCase(measurement_repo, contract_repo)
    measurement_dto = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="March Cloud Bill",
            gross_amount=Decimal("10000.00"),
        )
    )

    approve_use_case = ApproveMeasurementUseCase(measurement_repo)
    approved_dto = await approve_use_case.execute(
        ApproveMeasurementCommand(measurement_id=measurement_dto.id)
    )
    assert approved_dto.state == "APPROVED"

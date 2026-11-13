from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import (
    AllocationShareDTO,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.application.use_cases.commands import (
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import (
    AccountingAccountNotFoundError,
    AllocationDomainError,
)
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryAccountingAccountRepository,
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
)
from src.shared.domain.value_objects import AccountCode


@pytest.mark.asyncio
async def test_should_submit_measurement_with_override() -> None:
    sup_repo = InMemorySupplierRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()

    supplier = Supplier(name="Cloud Corp", tax_id="12.345.678/0001-90")
    await sup_repo.add(supplier)

    cc1, cc2, cc3 = uuid4(), uuid4(), uuid4()

    reg_contract_use_case = RegisterContractUseCase(contract_repo, sup_repo)
    contract_dto = await reg_contract_use_case.execute(
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

    submit_use_case = SubmitMeasurementUseCase(measurement_repo, contract_repo)
    measurement_dto = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="March Cloud Bill",
            gross_amount=Decimal("15000.00"),
            custom_allocations=[
                AllocationShareDTO(cost_center_id=cc1, percentage=Decimal("50.00")),
                AllocationShareDTO(cost_center_id=cc3, percentage=Decimal("50.00")),
            ],
        )
    )

    assert measurement_dto.state == "SUBMITTED"
    assert len(measurement_dto.entries) == 2
    assert measurement_dto.entries[0].amount == Decimal("7500.00")
    assert measurement_dto.entries[1].amount == Decimal("7500.00")


@pytest.mark.asyncio
async def test_should_submit_measurement_with_valid_accounting_account() -> None:
    accounting_account_repo = InMemoryAccountingAccountRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()
    supplier_repo = InMemorySupplierRepository()

    supplier = Supplier(name="Cloud Vendor", tax_id="00.111.222/0001-33")
    await supplier_repo.add(supplier)

    account = AccountingAccount(code=AccountCode("3.1.01"), name="Cloud Hosting")
    await accounting_account_repo.save(account)

    cc_id = uuid4()
    reg_contract = RegisterContractUseCase(contract_repo, supplier_repo)
    contract_dto = await reg_contract.execute(
        RegisterContractCommand(
            code="CT-CLOUD-01",
            supplier_id=supplier.id,
            title="Hosting Agreement",
            default_allocations=[
                AllocationShareDTO(
                    cost_center_id=cc_id,
                    percentage=Decimal("100.00"),
                    accounting_account_id=account.id,
                )
            ],
        )
    )

    submit_use_case = SubmitMeasurementUseCase(
        measurement_repo, contract_repo, accounting_account_repo
    )
    measurement_dto = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="March AWS Bill",
            gross_amount=Decimal("10000.00"),
        )
    )

    assert measurement_dto.state == "SUBMITTED"
    assert len(measurement_dto.entries) == 1
    assert measurement_dto.entries[0].accounting_account_id == account.id


@pytest.mark.asyncio
async def test_should_reject_measurement_with_non_existent_accounting_account() -> None:
    accounting_account_repo = InMemoryAccountingAccountRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()
    supplier_repo = InMemorySupplierRepository()

    supplier = Supplier(name="Vendor", tax_id="12.345.678/0001-99")
    await supplier_repo.add(supplier)

    reg_contract = RegisterContractUseCase(contract_repo, supplier_repo)
    contract_dto = await reg_contract.execute(
        RegisterContractCommand(
            code="CT-TEST-01",
            supplier_id=supplier.id,
            title="Test Agreement",
            default_allocations=[
                AllocationShareDTO(cost_center_id=uuid4(), percentage=Decimal("100.00"))
            ],
        )
    )

    submit_use_case = SubmitMeasurementUseCase(
        measurement_repo, contract_repo, accounting_account_repo
    )
    fake_account_id = uuid4()
    with pytest.raises(AccountingAccountNotFoundError):
        await submit_use_case.execute(
            SubmitMeasurementCommand(
                contract_id=contract_dto.id,
                period="2026-03",
                description="Invoice",
                gross_amount=Decimal("500.00"),
                custom_allocations=[
                    AllocationShareDTO(
                        cost_center_id=uuid4(),
                        percentage=Decimal("100.00"),
                        accounting_account_id=fake_account_id,
                    )
                ],
            )
        )


@pytest.mark.asyncio
async def test_should_reject_measurement_with_inactive_accounting_account() -> None:
    accounting_account_repo = InMemoryAccountingAccountRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()
    supplier_repo = InMemorySupplierRepository()

    supplier = Supplier(name="Vendor", tax_id="12.345.678/0001-99")
    await supplier_repo.add(supplier)

    account = AccountingAccount(
        code=AccountCode("3.9.99"), name="Legacy Category", is_active=False
    )
    await accounting_account_repo.save(account)

    reg_contract = RegisterContractUseCase(contract_repo, supplier_repo)
    contract_dto = await reg_contract.execute(
        RegisterContractCommand(
            code="CT-TEST-02",
            supplier_id=supplier.id,
            title="Test Agreement",
            default_allocations=[
                AllocationShareDTO(
                    cost_center_id=uuid4(),
                    percentage=Decimal("100.00"),
                    accounting_account_id=account.id,
                )
            ],
        )
    )

    submit_use_case = SubmitMeasurementUseCase(
        measurement_repo, contract_repo, accounting_account_repo
    )
    with pytest.raises(AllocationDomainError, match="is inactive"):
        await submit_use_case.execute(
            SubmitMeasurementCommand(
                contract_id=contract_dto.id,
                period="2026-03",
                description="Invoice",
                gross_amount=Decimal("500.00"),
            )
        )

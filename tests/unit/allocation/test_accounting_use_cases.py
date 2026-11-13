"""Unit tests for accounting account use cases."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import (
    AllocationShareDTO,
    ApproveMeasurementCommand,
    ListAccountingAccountsQuery,
    RegisterAccountingAccountCommand,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.application.use_cases import (
    ApproveMeasurementUseCase,
    GetCostCenterAccountingBreakdownUseCase,
    ListAccountingAccountsUseCase,
    RegisterAccountingAccountUseCase,
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import (
    AccountingAccountNotFoundError,
    AllocationDomainError,
    DuplicateAccountCodeError,
)
from src.allocation.infrastructure.repositories import (
    InMemoryAccountingAccountRepository,
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
)
from src.shared.domain.exceptions import InvalidAccountCodeError
from src.shared.domain.value_objects import AccountCode


@pytest.fixture
def accounting_account_repo() -> InMemoryAccountingAccountRepository:
    return InMemoryAccountingAccountRepository()


@pytest.fixture
def contract_repo() -> InMemoryContractRepository:
    return InMemoryContractRepository()


@pytest.fixture
def measurement_repo() -> InMemoryMeasurementRepository:
    return InMemoryMeasurementRepository()


@pytest.fixture
def supplier_repo() -> InMemorySupplierRepository:
    return InMemorySupplierRepository()


@pytest.mark.asyncio
async def test_should_register_accounting_account_successfully(
    accounting_account_repo: InMemoryAccountingAccountRepository,
) -> None:
    use_case = RegisterAccountingAccountUseCase(accounting_account_repo)
    command = RegisterAccountingAccountCommand(
        code="3.1.01",
        name="Software Licenses",
        description="SaaS tools",
    )

    dto = await use_case.execute(command)

    assert dto.code == "3.1.01"
    assert dto.name == "Software Licenses"
    assert dto.description == "SaaS tools"
    assert dto.is_active is True

    stored = await accounting_account_repo.get_by_id(dto.id)
    assert stored is not None
    assert stored.code == AccountCode("3.1.01")


@pytest.mark.asyncio
async def test_should_reject_duplicate_accounting_account_code(
    accounting_account_repo: InMemoryAccountingAccountRepository,
) -> None:
    use_case = RegisterAccountingAccountUseCase(accounting_account_repo)
    command = RegisterAccountingAccountCommand(code="3.1.01", name="Licenses")
    await use_case.execute(command)

    with pytest.raises(DuplicateAccountCodeError):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_should_reject_invalid_accounting_account_code(
    accounting_account_repo: InMemoryAccountingAccountRepository,
) -> None:
    use_case = RegisterAccountingAccountUseCase(accounting_account_repo)
    command = RegisterAccountingAccountCommand(code="invalid..code", name="Bad")

    with pytest.raises(InvalidAccountCodeError):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_should_list_accounting_accounts_with_pagination(
    accounting_account_repo: InMemoryAccountingAccountRepository,
) -> None:
    reg_use_case = RegisterAccountingAccountUseCase(accounting_account_repo)
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.1", name="Cat 1")
    )
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.2", name="Cat 2")
    )
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.3", name="Cat 3")
    )

    list_use_case = ListAccountingAccountsUseCase(accounting_account_repo)
    page1 = await list_use_case.execute(ListAccountingAccountsQuery(page=1, per_page=2))

    assert page1.total_items == 3
    assert len(page1.items) == 2
    assert page1.items[0].code == "3.1"
    assert page1.items[1].code == "3.2"

    page2 = await list_use_case.execute(ListAccountingAccountsQuery(page=2, per_page=2))
    assert len(page2.items) == 1
    assert page2.items[0].code == "3.3"


@pytest.mark.asyncio
async def test_should_submit_measurement_with_valid_accounting_account(
    accounting_account_repo: InMemoryAccountingAccountRepository,
    contract_repo: InMemoryContractRepository,
    measurement_repo: InMemoryMeasurementRepository,
    supplier_repo: InMemorySupplierRepository,
) -> None:
    # Setup supplier & contract
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
async def test_should_reject_measurement_with_non_existent_accounting_account(
    accounting_account_repo: InMemoryAccountingAccountRepository,
    contract_repo: InMemoryContractRepository,
    measurement_repo: InMemoryMeasurementRepository,
    supplier_repo: InMemorySupplierRepository,
) -> None:
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
async def test_should_reject_measurement_with_inactive_accounting_account(
    accounting_account_repo: InMemoryAccountingAccountRepository,
    contract_repo: InMemoryContractRepository,
    measurement_repo: InMemoryMeasurementRepository,
    supplier_repo: InMemorySupplierRepository,
) -> None:
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


@pytest.mark.asyncio
async def test_should_calculate_cost_center_accounting_breakdown(
    accounting_account_repo: InMemoryAccountingAccountRepository,
    contract_repo: InMemoryContractRepository,
    measurement_repo: InMemoryMeasurementRepository,
    supplier_repo: InMemorySupplierRepository,
) -> None:
    supplier = Supplier(name="Vendor Multi", tax_id="11.111.111/0001-11")
    await supplier_repo.add(supplier)

    acc_soft = AccountingAccount(code=AccountCode("3.1.01"), name="Software")
    acc_infra = AccountingAccount(code=AccountCode("3.1.02"), name="Infrastructure")
    await accounting_account_repo.save(acc_soft)
    await accounting_account_repo.save(acc_infra)

    target_cc_id = uuid4()
    other_cc_id = uuid4()

    reg_contract = RegisterContractUseCase(contract_repo, supplier_repo)
    contract_dto = await reg_contract.execute(
        RegisterContractCommand(
            code="CT-MULTI-01",
            supplier_id=supplier.id,
            title="Multi-spend",
            default_allocations=[
                AllocationShareDTO(
                    cost_center_id=target_cc_id,
                    percentage=Decimal("100.00"),
                )
            ],
        )
    )

    submit_use_case = SubmitMeasurementUseCase(
        measurement_repo, contract_repo, accounting_account_repo
    )
    approve_use_case = ApproveMeasurementUseCase(measurement_repo)

    # Submit & Approve Measurement 1: $6k to Software, $4k to Infrastructure
    m1 = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="Bill 1",
            gross_amount=Decimal("10000.00"),
            custom_allocations=[
                AllocationShareDTO(
                    cost_center_id=target_cc_id,
                    percentage=Decimal("60.00"),
                    accounting_account_id=acc_soft.id,
                ),
                AllocationShareDTO(
                    cost_center_id=target_cc_id,
                    percentage=Decimal("40.00"),
                    accounting_account_id=acc_infra.id,
                ),
            ],
        )
    )
    await approve_use_case.execute(ApproveMeasurementCommand(measurement_id=m1.id))

    # Submit & Approve Measurement 2 ($5,000): $5,000 to Software on target_cc
    m2 = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="Bill 2",
            gross_amount=Decimal("5000.00"),
            custom_allocations=[
                AllocationShareDTO(
                    cost_center_id=target_cc_id,
                    percentage=Decimal("100.00"),
                    accounting_account_id=acc_soft.id,
                ),
            ],
        )
    )
    await approve_use_case.execute(ApproveMeasurementCommand(measurement_id=m2.id))

    # Submit Unapproved Measurement ($2,000): Should be ignored
    await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="Draft Bill",
            gross_amount=Decimal("2000.00"),
            custom_allocations=[
                AllocationShareDTO(
                    cost_center_id=target_cc_id,
                    percentage=Decimal("100.00"),
                    accounting_account_id=acc_infra.id,
                )
            ],
        )
    )

    # Submit & Approve Measurement on OTHER cost center ($3,000): Should be ignored
    m_other = await submit_use_case.execute(
        SubmitMeasurementCommand(
            contract_id=contract_dto.id,
            period="2026-03",
            description="Other CC Bill",
            gross_amount=Decimal("3000.00"),
            custom_allocations=[
                AllocationShareDTO(
                    cost_center_id=other_cc_id,
                    percentage=Decimal("100.00"),
                    accounting_account_id=acc_soft.id,
                )
            ],
        )
    )
    await approve_use_case.execute(ApproveMeasurementCommand(measurement_id=m_other.id))

    # Execute breakdown use case
    breakdown_use_case = GetCostCenterAccountingBreakdownUseCase(
        measurement_repo, accounting_account_repo
    )
    breakdown = await breakdown_use_case.execute(target_cc_id, "2026-03")

    assert breakdown.cost_center_id == target_cc_id
    assert breakdown.period == "2026-03"
    assert breakdown.total_spent == Decimal("15000.00")
    assert len(breakdown.accounts) == 2

    # Top spent account: Software ($11,000 -> 73.33%)
    assert breakdown.accounts[0].account_code == "3.1.01"
    assert breakdown.accounts[0].account_name == "Software"
    assert breakdown.accounts[0].spent_amount == Decimal("11000.00")
    assert breakdown.accounts[0].share_pct == Decimal("73.33")

    # Second account: Infrastructure ($4,000 -> 26.67%)
    assert breakdown.accounts[1].account_code == "3.1.02"
    assert breakdown.accounts[1].account_name == "Infrastructure"
    assert breakdown.accounts[1].spent_amount == Decimal("4000.00")
    assert breakdown.accounts[1].share_pct == Decimal("26.67")

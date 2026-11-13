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
from src.allocation.application.use_cases.queries import (
    GetCostCenterAccountingBreakdownUseCase,
)
from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.infrastructure.repositories import (
    InMemoryAccountingAccountRepository,
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
)
from src.shared.domain.value_objects import AccountCode


@pytest.mark.asyncio
async def test_should_calculate_cost_center_accounting_breakdown() -> None:
    supplier_repo = InMemorySupplierRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()
    accounting_account_repo = InMemoryAccountingAccountRepository()

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

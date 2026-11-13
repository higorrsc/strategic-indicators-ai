"""Integration tests for AccountingAccount SQLAlchemy database persistence."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import AllocationEntry, Measurement
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import DuplicateAccountCodeError
from src.allocation.infrastructure.repositories import (
    SqlAlchemyAccountingAccountRepository,
    SqlAlchemyContractRepository,
    SqlAlchemyMeasurementRepository,
    SqlAlchemySupplierRepository,
)
from src.shared.domain.value_objects import (
    AccountCode,
    Money,
    Percentage,
    Period,
)


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_accounting_account(
    db_session: AsyncSession,
) -> None:
    """Verify storing and retrieving accounting accounts."""
    repo = SqlAlchemyAccountingAccountRepository(db_session)
    account = AccountingAccount(
        code=AccountCode("3.1.01"),
        name="Software Licenses",
        description="SaaS and On-premise licenses",
    )

    await repo.save(account)
    by_id = await repo.get_by_id(account.id)
    assert by_id is not None
    assert by_id.id == account.id
    assert by_id.code == AccountCode("3.1.01")
    assert by_id.name == "Software Licenses"
    assert by_id.is_active is True

    by_code = await repo.get_by_code(AccountCode("3.1.01"))
    assert by_code is not None
    assert by_code.id == account.id


@pytest.mark.asyncio
async def test_should_update_existing_accounting_account(
    db_session: AsyncSession,
) -> None:
    """Verify updating details and deactivating accounting account."""
    repo = SqlAlchemyAccountingAccountRepository(db_session)
    account = AccountingAccount(
        code=AccountCode("3.1.02"),
        name="Cloud Compute",
        description="AWS / GCP",
    )
    await repo.save(account)

    account.update_details("Cloud Infrastructure & Compute", "Updated description")
    account.deactivate()
    await repo.save(account)

    updated = await repo.get_by_id(account.id)
    assert updated is not None
    assert updated.name == "Cloud Infrastructure & Compute"
    assert updated.description == "Updated description"
    assert not updated.is_active


@pytest.mark.asyncio
async def test_should_reject_duplicate_accounting_account_code(
    db_session: AsyncSession,
) -> None:
    """Verify uniqueness constraint on account code."""
    repo = SqlAlchemyAccountingAccountRepository(db_session)
    acc1 = AccountingAccount(code=AccountCode("3.2.01"), name="Hardware")
    await repo.save(acc1)

    acc2 = AccountingAccount(code=AccountCode("3.2.01"), name="Duplicate Hardware")
    with pytest.raises(DuplicateAccountCodeError):
        await repo.save(acc2)


@pytest.mark.asyncio
async def test_should_list_and_count_accounting_accounts_with_pagination(
    db_session: AsyncSession,
) -> None:
    """Verify paginated listing and count filtering."""
    repo = SqlAlchemyAccountingAccountRepository(db_session)
    acc_active1 = AccountingAccount(code=AccountCode("3.3.01"), name="Consulting A")
    acc_active2 = AccountingAccount(code=AccountCode("3.3.02"), name="Consulting B")
    acc_inactive = AccountingAccount(
        code=AccountCode("3.3.03"), name="Retired Service", is_active=False
    )

    await repo.save(acc_active1)
    await repo.save(acc_active2)
    await repo.save(acc_inactive)

    active_count = await repo.count(active_only=True)
    all_count = await repo.count(active_only=False)
    assert active_count >= 2
    assert all_count >= 3

    page = await repo.list_all(active_only=True, offset=0, limit=2)
    assert len(page) <= 2


@pytest.mark.asyncio
async def test_should_persist_measurement_with_accounting_account_id(
    db_session: AsyncSession,
) -> None:
    """Verify measurement entry persistence with accounting account reference."""
    acc_repo = SqlAlchemyAccountingAccountRepository(db_session)
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)
    meas_repo = SqlAlchemyMeasurementRepository(db_session)

    account = AccountingAccount(code=AccountCode("4.1.01"), name="IT Telecom")
    await acc_repo.save(account)

    supplier = Supplier(name="Telecom Corp", tax_id="11.222.333/0001-44")
    await sup_repo.add(supplier)

    contract = Contract(
        code="CT-TEL-2026",
        supplier_id=supplier.id,
        title="Telecom Services",
        default_allocations=[
            AllocationShare(
                cost_center_id=uuid4(),
                percentage=Percentage(Decimal("100.00")),
                accounting_account_id=account.id,
            )
        ],
    )
    await contract_repo.add(contract)

    measurement = Measurement(
        contract_id=contract.id,
        period=Period(2026, 3),
        description="March Telecom Invoice",
        gross_amount=Money(Decimal("5000.00"), "USD"),
        entries=[
            AllocationEntry(
                cost_center_id=uuid4(),
                amount=Money(Decimal("5000.00"), "USD"),
                percentage=Percentage(Decimal("100.00")),
                accounting_account_id=account.id,
            )
        ],
    )
    await meas_repo.add(measurement)

    retrieved = await meas_repo.get_by_id(measurement.id)
    assert retrieved is not None
    assert len(retrieved.entries) == 1
    assert retrieved.entries[0].accounting_account_id == account.id

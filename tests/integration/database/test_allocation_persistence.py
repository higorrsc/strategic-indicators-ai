"""Integration tests for Cost Allocation SQLAlchemy database persistence."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.infrastructure.repositories import (
    sqlalchemy_allocation_repository as sa_repo,
)
from src.shared.domain.value_objects import Money, Percentage, Period

SqlAlchemyContractRepository = sa_repo.SqlAlchemyContractRepository
SqlAlchemyMeasurementRepository = sa_repo.SqlAlchemyMeasurementRepository
SqlAlchemySupplierRepository = sa_repo.SqlAlchemySupplierRepository


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_supplier(
    db_session: AsyncSession,
) -> None:
    """Verify persisting and querying suppliers via SQLAlchemy."""
    repo = SqlAlchemySupplierRepository(db_session)
    supplier = Supplier(name="Acme Cloud Services", tax_id="12.345.678/0001-90")

    await repo.add(supplier)
    retrieved = await repo.get_by_id(supplier.id)

    assert retrieved is not None
    assert retrieved.id == supplier.id
    assert retrieved.name == "Acme Cloud Services"
    assert retrieved.tax_id == "12.345.678/0001-90"

    all_suppliers = await repo.list_all()
    assert len(all_suppliers) >= 1
    assert any(s.id == supplier.id for s in all_suppliers)


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_contract_with_default_allocations(
    db_session: AsyncSession,
) -> None:
    """Verify storing and retrieving a contract with default allocation shares."""
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)

    supplier = Supplier(name="Network Provider", tax_id="98.765.432/0001-10")
    await sup_repo.add(supplier)

    cc1_id = uuid4()
    cc2_id = uuid4()

    contract = Contract(
        code="CT-2026-PERSIST-01",
        supplier_id=supplier.id,
        title="Fiber Optic Connectivity",
        default_allocations=[
            AllocationShare(
                cost_center_id=cc1_id,
                percentage=Percentage(Decimal("60.00")),
            ),
            AllocationShare(
                cost_center_id=cc2_id,
                percentage=Percentage(Decimal("40.00")),
            ),
        ],
    )
    await contract_repo.add(contract)

    retrieved = await contract_repo.get_by_id(contract.id)
    assert retrieved is not None
    assert retrieved.id == contract.id
    assert retrieved.code == "CT-2026-PERSIST-01"
    assert retrieved.supplier_id == supplier.id
    assert len(retrieved.default_allocations) == 2

    by_code = await contract_repo.get_by_code("CT-2026-PERSIST-01")
    assert by_code is not None
    assert by_code.id == contract.id


@pytest.mark.asyncio
async def test_should_update_contract(
    db_session: AsyncSession,
) -> None:
    """Verify modifying a contract entity."""
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)

    supplier = Supplier(name="Hardware Vendor", tax_id="11.222.333/0001-44")
    await sup_repo.add(supplier)

    contract = Contract(
        code="CT-2026-UPDATE-01",
        supplier_id=supplier.id,
        title="Initial Title",
    )
    await contract_repo.add(contract)

    contract.title = "Amended Title"
    contract.is_active = False
    await contract_repo.update(contract)

    updated = await contract_repo.get_by_id(contract.id)
    assert updated is not None
    assert updated.title == "Amended Title"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_measurement_with_entries(
    db_session: AsyncSession,
) -> None:
    """Verify persisting and loading measurement aggregate with allocation entries."""
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)
    measurement_repo = SqlAlchemyMeasurementRepository(db_session)

    supplier = Supplier(name="Software License Co", tax_id="33.444.555/0001-66")
    await sup_repo.add(supplier)

    contract = Contract(
        code="CT-2026-MEAS-01",
        supplier_id=supplier.id,
        title="Enterprise SaaS",
    )
    await contract_repo.add(contract)

    cc1_id = uuid4()
    cc2_id = uuid4()

    measurement = Measurement(
        contract_id=contract.id,
        period=Period.from_string("2026-05"),
        description="Monthly SaaS billing",
        gross_amount=Money(Decimal("10000.00")),
    )
    entries = [
        AllocationEntry(
            cost_center_id=cc1_id,
            amount=Money(Decimal("6000.00")),
            percentage=Percentage(Decimal("60.00")),
        ),
        AllocationEntry(
            cost_center_id=cc2_id,
            amount=Money(Decimal("4000.00")),
            percentage=Percentage(Decimal("40.00")),
        ),
    ]
    measurement.set_entries(entries)
    await measurement_repo.add(measurement)

    retrieved = await measurement_repo.get_by_id(measurement.id)
    assert retrieved is not None
    assert retrieved.id == measurement.id
    assert retrieved.contract_id == contract.id
    assert retrieved.period == Period.from_string("2026-05")
    assert retrieved.gross_amount == Money(Decimal("10000.00"))
    assert retrieved.state == MeasurementState.DRAFT
    assert len(retrieved.entries) == 2
    assert sum(e.amount.amount for e in retrieved.entries) == Decimal("10000.00")


@pytest.mark.asyncio
async def test_should_list_measurements_by_period_and_contract(
    db_session: AsyncSession,
) -> None:
    """Verify querying measurements by period and contract."""
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)
    measurement_repo = SqlAlchemyMeasurementRepository(db_session)

    supplier = Supplier(name="Consulting Group", tax_id="55.666.777/0001-88")
    await sup_repo.add(supplier)

    contract = Contract(
        code="CT-2026-LIST-01",
        supplier_id=supplier.id,
        title="IT Advisory",
    )
    await contract_repo.add(contract)

    m1 = Measurement(
        contract_id=contract.id,
        period=Period.from_string("2026-06"),
        description="Phase 1",
        gross_amount=Money(Decimal("25000.00")),
    )
    await measurement_repo.add(m1)

    period_matches = await measurement_repo.list_by_period(
        Period.from_string("2026-06")
    )
    assert len(period_matches) >= 1
    assert any(m.id == m1.id for m in period_matches)

    contract_matches = await measurement_repo.list_by_contract(contract.id)
    assert len(contract_matches) >= 1
    assert any(m.id == m1.id for m in contract_matches)


@pytest.mark.asyncio
async def test_should_update_measurement_state_and_entries(
    db_session: AsyncSession,
) -> None:
    """Verify updating measurement status and allocation entries."""
    sup_repo = SqlAlchemySupplierRepository(db_session)
    contract_repo = SqlAlchemyContractRepository(db_session)
    measurement_repo = SqlAlchemyMeasurementRepository(db_session)

    supplier = Supplier(name="Logistics Vendor", tax_id="77.888.999/0001-00")
    await sup_repo.add(supplier)

    contract = Contract(
        code="CT-2026-UPDATE-MEAS",
        supplier_id=supplier.id,
        title="Freight Services",
    )
    await contract_repo.add(contract)

    measurement = Measurement(
        contract_id=contract.id,
        period=Period.from_string("2026-07"),
        description="Delivery invoice",
        gross_amount=Money(Decimal("5000.00")),
    )
    cc_id = uuid4()
    measurement.set_entries(
        [
            AllocationEntry(
                cost_center_id=cc_id,
                amount=Money(Decimal("5000.00")),
                percentage=Percentage(Decimal("100.00")),
            )
        ]
    )
    await measurement_repo.add(measurement)

    # Transition state to SUBMITTED and then APPROVED
    measurement.submit()
    measurement.approve()
    await measurement_repo.update(measurement)

    updated = await measurement_repo.get_by_id(measurement.id)
    assert updated is not None
    assert updated.state == MeasurementState.APPROVED
    assert len(updated.entries) == 1

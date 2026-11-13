from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.exceptions import InvalidMeasurementStateError
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryMeasurementRepository,
)
from src.shared.domain.value_objects import Money, Percentage, Period


def test_should_reject_invalid_measurement_state_transition() -> None:
    measurement = Measurement(
        contract_id=uuid4(),
        period=Period.from_string("2026-03"),
        description="March Hosting",
        gross_amount=Money.from_float_or_int(1000),
    )
    assert measurement.state == MeasurementState.DRAFT
    with pytest.raises(InvalidMeasurementStateError):
        measurement.approve()


@pytest.mark.asyncio
async def test_should_filter_measurements_by_criteria() -> None:
    repo = InMemoryMeasurementRepository()
    ct1, ct2 = uuid4(), uuid4()
    cc_id = uuid4()

    m1 = Measurement(
        contract_id=ct1,
        period=Period(2026, 4),
        description="M1",
        gross_amount=Money(Decimal("100.00")),
    )
    m1.set_entries(
        [
            AllocationEntry(
                cost_center_id=cc_id,
                amount=Money(Decimal("100.00")),
                percentage=Percentage(Decimal("100.00")),
            )
        ]
    )
    m1.submit()
    m1.approve()
    await repo.add(m1)

    m2 = Measurement(
        contract_id=ct1,
        period=Period(2026, 4),
        description="M2",
        gross_amount=Money(Decimal("200.00")),
    )
    m2.set_entries(
        [
            AllocationEntry(
                cost_center_id=cc_id,
                amount=Money(Decimal("200.00")),
                percentage=Percentage(Decimal("100.00")),
            )
        ]
    )
    m2.submit()
    await repo.add(m2)

    m3 = Measurement(
        contract_id=ct2,
        period=Period(2026, 5),
        description="M3",
        gross_amount=Money(Decimal("300.00")),
    )
    await repo.add(m3)

    assert len(await repo.find(period=Period(2026, 4))) == 2
    assert len(await repo.find(contract_id=ct1, state=MeasurementState.APPROVED)) == 1
    assert len(await repo.find(period=Period(2026, 5))) == 1
    assert len(await repo.find(contract_id=uuid4())) == 0

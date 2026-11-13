from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.application.dto import ListMeasurementsQuery
from src.allocation.application.use_cases.queries import ListMeasurementsUseCase
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
)
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryMeasurementRepository,
)
from src.shared.domain.value_objects import Money, Percentage, Period


@pytest.mark.asyncio
async def test_should_list_measurements_with_filters() -> None:
    repo = InMemoryMeasurementRepository()
    ct1 = uuid4()
    cc_id = uuid4()

    m1 = Measurement(
        contract_id=ct1,
        period=Period(2026, 3),
        description="March Bill",
        gross_amount=Money(Decimal("1000.00")),
    )
    m1.set_entries(
        [
            AllocationEntry(
                cost_center_id=cc_id,
                amount=Money(Decimal("1000.00")),
                percentage=Percentage(Decimal("100.00")),
            )
        ]
    )
    m1.submit()
    m1.approve()
    await repo.add(m1)

    use_case = ListMeasurementsUseCase(repo)

    res = await use_case.execute(ListMeasurementsQuery(period="2026-03"))
    assert len(res.items) == 1
    assert res.total_items == 1
    assert res.page == 1
    assert res.per_page == 20
    assert res.items[0].description == "March Bill"
    assert res.items[0].state == "APPROVED"
    assert len(res.items[0].entries) == 1

from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryMeasurementRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)
from src.indicators.application.dto import ComputePeriodIndicatorsQuery
from src.indicators.application.use_cases.queries import (
    ComputePeriodIndicatorsUseCase,
)
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
)


@pytest.mark.asyncio
async def test_should_compute_period_indicators() -> None:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    measurement_repo = InMemoryMeasurementRepository()

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="Engineering")
    await cc_repo.add(cc1)

    period = Period.from_string("2026-03")

    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc1.id,
            period=period,
            category="Cloud",
            amount=Money.from_float_or_int(20000),
        )
    )

    contract = Contract(
        code="CT-AWS",
        supplier_id=uuid4(),
        title="AWS Cloud",
        default_allocations=[
            AllocationShare(cost_center_id=cc1.id, percentage=Percentage.hundred())
        ],
    )

    measurement = Measurement(
        contract_id=contract.id,
        period=period,
        description="March AWS Invoice",
        gross_amount=Money.from_float_or_int(16000),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money.from_float_or_int(16000),
                percentage=Percentage.hundred(),
            )
        ],
    )
    await measurement_repo.add(measurement)

    indicators_use_case = ComputePeriodIndicatorsUseCase(
        cc_repo, budget_repo, measurement_repo
    )
    dto = await indicators_use_case.execute(
        ComputePeriodIndicatorsQuery(period="2026-03")
    )

    assert dto.total_budgeted == Decimal("20000.00")
    assert dto.total_actual == Decimal("16000.00")
    assert dto.total_variance == Decimal("-4000.00")
    assert dto.total_execution_rate == Decimal("80.00")
    assert len(dto.indicators) == 1
    assert dto.indicators[0].status == "NORMAL"

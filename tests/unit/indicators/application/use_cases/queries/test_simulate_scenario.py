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
from src.indicators.application.dto import SimulateScenarioCommand
from src.indicators.application.use_cases.queries import (
    SimulateScenarioUseCase,
)
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
)


@pytest.mark.asyncio
async def test_should_simulate_scenario_price_increase() -> None:
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

    simulate_use_case = SimulateScenarioUseCase(cc_repo, budget_repo, measurement_repo)
    sim_result = await simulate_use_case.execute(
        SimulateScenarioCommand(
            scenario_name="AWS Price Surge",
            period="2026-03",
            contract_cost_adjustments={contract.id: Decimal("30.00")},
        )
    )

    assert sim_result.scenario_name == "AWS Price Surge"
    impact = sim_result.impacts[0]
    # 16000 * 1.30 = 20800 > 20000 -> OVERRUN
    assert impact.simulated_actual == Decimal("20800.00")
    assert impact.new_overrun is True
    assert impact.simulated_status == "CRITICAL_OVERRUN"

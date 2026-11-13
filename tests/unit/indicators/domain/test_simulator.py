from uuid import uuid4

from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.indicators.domain.models import IndicatorStatus
from src.indicators.domain.services.simulator import (
    AllocationShift,
    WhatIfSimulator,
)
from src.shared.domain.value_objects import Money, Percentage, Period


def test_should_simulate_cost_increase_and_detect_new_overrun() -> None:
    cc1 = uuid4()
    period = Period.from_string("2026-03")
    contract_id = uuid4()

    budgets = [
        BudgetTarget(
            cost_center_id=cc1,
            period=period,
            category="IT Operations",
            amount=Money.from_float_or_int(10000),
        )
    ]

    measurement = Measurement(
        contract_id=contract_id,
        period=period,
        description="Software License",
        gross_amount=Money.from_float_or_int(9000),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1,
                amount=Money.from_float_or_int(9000),
                percentage=Percentage.hundred(),
            )
        ],
    )

    result = WhatIfSimulator.simulate(
        scenario_name="Inflation +20%",
        period=period,
        cost_centers={cc1: "1.1"},
        budgets=budgets,
        measurements=[measurement],
        contract_cost_adjustments={contract_id: Percentage.from_number("20.00")},
    )

    impact = result.impacts[0]
    assert impact.baseline_status == IndicatorStatus.WARNING
    assert impact.simulated_status == IndicatorStatus.CRITICAL_OVERRUN
    assert impact.new_overrun is True
    assert impact.simulated_actual == Money.from_float_or_int(10800)
    assert impact.delta_actual == Money.from_float_or_int(1800)


def test_should_simulate_allocation_shift_between_centers() -> None:
    cc1, cc2 = uuid4(), uuid4()
    period = Period.from_string("2026-03")
    contract_id = uuid4()

    budgets = [
        BudgetTarget(
            cost_center_id=cc1,
            period=period,
            category="Dev",
            amount=Money.from_float_or_int(10000),
        ),
        BudgetTarget(
            cost_center_id=cc2,
            period=period,
            category="Ops",
            amount=Money.from_float_or_int(10000),
        ),
    ]

    measurement = Measurement(
        contract_id=contract_id,
        period=period,
        description="Shared Infrastructure",
        gross_amount=Money.from_float_or_int(10000),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1,
                amount=Money.from_float_or_int(5000),
                percentage=Percentage.from_number("50.00"),
            ),
            AllocationEntry(
                cost_center_id=cc2,
                amount=Money.from_float_or_int(5000),
                percentage=Percentage.from_number("50.00"),
            ),
        ],
    )

    shift = AllocationShift(
        from_cost_center_id=cc1,
        to_cost_center_id=cc2,
        percentage_points=Percentage.from_number("20.00"),
    )

    result = WhatIfSimulator.simulate(
        scenario_name="Reallocation to Ops",
        period=period,
        cost_centers={cc1: "1.1", cc2: "1.2"},
        budgets=budgets,
        measurements=[measurement],
        allocation_shifts=[shift],
    )

    impacts_by_cc = {imp.cost_center_id: imp for imp in result.impacts}
    assert impacts_by_cc[cc1].simulated_actual == Money.from_float_or_int(3000)
    assert impacts_by_cc[cc2].simulated_actual == Money.from_float_or_int(7000)

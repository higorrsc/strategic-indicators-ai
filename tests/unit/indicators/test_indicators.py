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
from src.indicators.application.dto import (
    ComputePeriodIndicatorsQuery,
    SimulateScenarioCommand,
)
from src.indicators.application.use_cases import (
    ComputePeriodIndicatorsUseCase,
    SimulateScenarioUseCase,
)
from src.indicators.domain.models import IndicatorStatus
from src.indicators.domain.services.simulator import (
    AllocationShift,
    WhatIfSimulator,
)
from src.indicators.domain.services.variance_calculator import (
    BudgetVarianceCalculator,
)
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
)


class TestBudgetVarianceCalculator:
    def test_should_classify_normal_status(self) -> None:
        cc_id = uuid4()
        period = Period.from_string("2026-03")
        budgeted = Money.from_float_or_int(10000)
        actual = Money.from_float_or_int(7500)

        ind = BudgetVarianceCalculator.calculate(
            cost_center_id=cc_id,
            cost_center_code="1.1",
            period=period,
            budgeted_amount=budgeted,
            actual_amount=actual,
        )

        assert ind.status == IndicatorStatus.NORMAL
        assert ind.variance_amount == Money.from_float_or_int(-2500)
        assert ind.execution_rate == Percentage.from_number("75.00")

    def test_should_classify_warning_status(self) -> None:
        cc_id = uuid4()
        period = Period.from_string("2026-03")
        budgeted = Money.from_float_or_int(10000)
        actual = Money.from_float_or_int(9500)

        ind = BudgetVarianceCalculator.calculate(
            cost_center_id=cc_id,
            cost_center_code="1.1",
            period=period,
            budgeted_amount=budgeted,
            actual_amount=actual,
        )

        assert ind.status == IndicatorStatus.WARNING
        assert ind.execution_rate == Percentage.from_number("95.00")

    def test_should_classify_overrun_status(self) -> None:
        cc_id = uuid4()
        period = Period.from_string("2026-03")
        budgeted = Money.from_float_or_int(10000)
        actual = Money.from_float_or_int(11500)

        ind = BudgetVarianceCalculator.calculate(
            cost_center_id=cc_id,
            cost_center_code="1.1",
            period=period,
            budgeted_amount=budgeted,
            actual_amount=actual,
        )

        assert ind.status == IndicatorStatus.CRITICAL_OVERRUN
        assert ind.variance_amount == Money.from_float_or_int(1500)
        assert ind.execution_rate == Percentage.from_number("115.00")


class TestWhatIfSimulator:
    def test_should_simulate_cost_increase_and_detect_new_overrun(self) -> None:
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

        # Baseline: 9000 / 10000 = 90% (WARNING)
        # Simulation: +20% inflation on contract -> 9000 * 1.20 = 10800 (OVERRUN!)
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

    def test_should_simulate_allocation_shift_between_centers(self) -> None:
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

        # Initial measurement: 10000 total (50% CC1, 50% CC2) -> 5000 each
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

        # Shift 20% from CC1 to CC2:
        # CC1 will have 30% (3000), CC2 will have 70% (7000)
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


@pytest.mark.asyncio
class TestIndicatorsUseCases:
    async def test_should_compute_period_indicators_and_simulate(self) -> None:
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

        # 1. Compute Period Indicators
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

        # 2. Simulate +30% Cloud Price Increase
        simulate_use_case = SimulateScenarioUseCase(
            cc_repo, budget_repo, measurement_repo
        )
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

from uuid import uuid4

from src.indicators.domain.models import IndicatorStatus
from src.indicators.domain.services.variance_calculator import (
    BudgetVarianceCalculator,
)
from src.shared.domain.value_objects import Money, Percentage, Period


def test_should_classify_normal_status() -> None:
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


def test_should_classify_warning_status() -> None:
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


def test_should_classify_overrun_status() -> None:
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

from decimal import Decimal
from uuid import uuid4

import pytest

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.exceptions import InvalidBudgetTargetError
from src.shared.domain.value_objects import Money, Period


def test_should_create_valid_budget_target() -> None:
    cc_id = uuid4()
    period = Period.from_string("2026-03")
    target = BudgetTarget(
        cost_center_id=cc_id,
        period=period,
        category="Cloud Infrastructure",
        amount=Money.from_float_or_int(50000, "USD"),
    )
    assert target.amount.amount == Decimal("50000.00")


def test_should_reject_negative_budget_target() -> None:
    cc_id = uuid4()
    period = Period.from_string("2026-03")
    with pytest.raises(InvalidBudgetTargetError):
        BudgetTarget(
            cost_center_id=cc_id,
            period=period,
            category="Hardware",
            amount=Money(Decimal("-10.00"), "USD"),
        )

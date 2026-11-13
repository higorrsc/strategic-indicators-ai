from uuid import uuid4

import pytest

from src.allocation.domain.entities.contract import AllocationShare
from src.allocation.domain.exceptions import InvalidAllocationPercentageError
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.shared.domain.value_objects import Money, Percentage


def test_should_reconcile_rounding_across_three_shares() -> None:
    cc1, cc2, cc3 = uuid4(), uuid4(), uuid4()
    shares = [
        AllocationShare(cost_center_id=cc1, percentage=Percentage.from_number("33.33")),
        AllocationShare(cost_center_id=cc2, percentage=Percentage.from_number("33.33")),
        AllocationShare(cost_center_id=cc3, percentage=Percentage.from_number("33.34")),
    ]
    gross = Money.from_float_or_int(1000, "USD")
    entries = ExactPennyAllocator.allocate(gross, shares)

    total_allocated = sum((e.amount for e in entries), Money.zero("USD"))
    assert total_allocated == gross
    assert len(entries) == 3


def test_should_reject_shares_not_summing_to_hundred() -> None:
    shares = [
        AllocationShare(
            cost_center_id=uuid4(), percentage=Percentage.from_number("50.00")
        ),
        AllocationShare(
            cost_center_id=uuid4(), percentage=Percentage.from_number("45.00")
        ),
    ]
    with pytest.raises(InvalidAllocationPercentageError):
        ExactPennyAllocator.allocate(Money.from_float_or_int(100), shares)

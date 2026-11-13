from uuid import uuid4

from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.shared.domain.value_objects import Percentage


def test_should_enforce_contract_default_allocation_integrity() -> None:
    sup_id = uuid4()
    cc1, cc2 = uuid4(), uuid4()
    valid_shares = [
        AllocationShare(cost_center_id=cc1, percentage=Percentage.from_number("70.00")),
        AllocationShare(cost_center_id=cc2, percentage=Percentage.from_number("30.00")),
    ]
    contract = Contract(
        code="CT-001",
        supplier_id=sup_id,
        title="Cloud Hosting",
        default_allocations=valid_shares,
    )
    assert len(contract.default_allocations) == 2

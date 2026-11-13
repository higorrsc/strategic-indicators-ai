from uuid import uuid4

import pytest

from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.exceptions import (
    CircularCostCenterHierarchyError,
    InvalidBudgetTargetError,
)
from src.shared.domain.value_objects import CostCenterCode


def test_should_create_cost_center() -> None:
    cc = CostCenter(code=CostCenterCode("1.0"), name="Executive Board")
    assert cc.name == "Executive Board"
    assert cc.is_active is True
    assert cc.parent_id is None


def test_should_reject_empty_name() -> None:
    with pytest.raises(InvalidBudgetTargetError):
        CostCenter(code=CostCenterCode("1.0"), name="   ")


def test_should_prevent_self_parenting() -> None:
    same_id = uuid4()
    with pytest.raises(CircularCostCenterHierarchyError):
        CostCenter(
            id=same_id,
            code=CostCenterCode("1.0"),
            name="Board",
            parent_id=same_id,
        )


def test_should_activate_and_deactivate() -> None:
    cc = CostCenter(code=CostCenterCode("1.0"), name="Board")
    cc.deactivate()
    assert not cc.is_active
    cc.activate()
    assert cc.is_active

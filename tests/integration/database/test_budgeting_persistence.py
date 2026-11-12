"""Integration tests for Budgeting SQLAlchemy database persistence."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.infrastructure.repositories.sqlalchemy_budgeting_repository import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyCostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode, Money, Period


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_cost_center(
    db_session: AsyncSession,
) -> None:
    """Verify persisting and retrieving a cost center via SQLAlchemy."""
    repo = SqlAlchemyCostCenterRepository(db_session)
    cc = CostCenter(code=CostCenterCode("1.1"), name="Engineering")

    await repo.add(cc)
    retrieved = await repo.get_by_id(cc.id)

    assert retrieved is not None
    assert retrieved.id == cc.id
    assert retrieved.code == CostCenterCode("1.1")
    assert retrieved.name == "Engineering"
    assert retrieved.parent_id is None
    assert retrieved.is_active is True


@pytest.mark.asyncio
async def test_should_retrieve_cost_center_by_code(
    db_session: AsyncSession,
) -> None:
    """Verify retrieving a cost center by its hierarchical code."""
    repo = SqlAlchemyCostCenterRepository(db_session)
    cc = CostCenter(code=CostCenterCode("2.1"), name="Marketing")

    await repo.add(cc)
    retrieved = await repo.get_by_code(CostCenterCode("2.1"))

    assert retrieved is not None
    assert retrieved.id == cc.id
    assert retrieved.name == "Marketing"


@pytest.mark.asyncio
async def test_should_retrieve_children_and_descendants(
    db_session: AsyncSession,
) -> None:
    """Verify hierarchy navigation methods for children and descendants."""
    repo = SqlAlchemyCostCenterRepository(db_session)
    root = CostCenter(code=CostCenterCode("1"), name="Corporate")
    child = CostCenter(code=CostCenterCode("1.1"), name="Operations", parent_id=root.id)
    grandchild = CostCenter(
        code=CostCenterCode("1.1.1"), name="Plant", parent_id=child.id
    )

    await repo.add(root)
    await repo.add(child)
    await repo.add(grandchild)

    children = await repo.get_children(root.id)
    assert len(children) == 1
    assert children[0].id == child.id

    descendants = await repo.get_descendants(root.id)
    assert len(descendants) == 2
    descendant_ids = {d.id for d in descendants}
    assert child.id in descendant_ids
    assert grandchild.id in descendant_ids


@pytest.mark.asyncio
async def test_should_update_cost_center(
    db_session: AsyncSession,
) -> None:
    """Verify updating an existing cost center."""
    repo = SqlAlchemyCostCenterRepository(db_session)
    cc = CostCenter(code=CostCenterCode("3.1"), name="Old Name")
    await repo.add(cc)

    cc.name = "New Name"
    cc.deactivate()
    await repo.update(cc)

    updated = await repo.get_by_id(cc.id)
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_should_persist_and_retrieve_budget_target(
    db_session: AsyncSession,
) -> None:
    """Verify persisting and querying budget targets via SQLAlchemy."""
    cc_repo = SqlAlchemyCostCenterRepository(db_session)
    budget_repo = SqlAlchemyBudgetRepository(db_session)

    cc = CostCenter(code=CostCenterCode("4.1"), name="R&D")
    await cc_repo.add(cc)

    target = BudgetTarget(
        cost_center_id=cc.id,
        period=Period.from_string("2026-03"),
        category="OPEX",
        amount=Money(Decimal("75000.00")),
    )
    await budget_repo.add(target)

    retrieved = await budget_repo.get_by_id(target.id)
    assert retrieved is not None
    assert retrieved.id == target.id
    assert retrieved.cost_center_id == cc.id
    assert retrieved.period == Period.from_string("2026-03")
    assert retrieved.category == "OPEX"
    assert retrieved.amount == Money(Decimal("75000.00"))


@pytest.mark.asyncio
async def test_should_filter_budget_targets_by_cost_center_and_period(
    db_session: AsyncSession,
) -> None:
    """Verify filtering budget targets by cost center and period."""
    cc_repo = SqlAlchemyCostCenterRepository(db_session)
    budget_repo = SqlAlchemyBudgetRepository(db_session)

    cc = CostCenter(code=CostCenterCode("5.1"), name="Finance")
    await cc_repo.add(cc)

    t1 = BudgetTarget(
        cost_center_id=cc.id,
        period=Period.from_string("2026-01"),
        category="OPEX",
        amount=Money(Decimal("10000.00")),
    )
    t2 = BudgetTarget(
        cost_center_id=cc.id,
        period=Period.from_string("2026-02"),
        category="CAPEX",
        amount=Money(Decimal("20000.00")),
    )
    await budget_repo.add(t1)
    await budget_repo.add(t2)

    p1_targets = await budget_repo.get_by_cost_center_and_period(
        cc.id, Period.from_string("2026-01")
    )
    assert len(p1_targets) == 1
    assert p1_targets[0].id == t1.id

    all_p2 = await budget_repo.list_by_period(Period.from_string("2026-02"))
    assert len(all_p2) >= 1
    assert any(b.id == t2.id for b in all_p2)


@pytest.mark.asyncio
async def test_should_update_budget_target(
    db_session: AsyncSession,
) -> None:
    """Verify modifying a budget target."""
    cc_repo = SqlAlchemyCostCenterRepository(db_session)
    budget_repo = SqlAlchemyBudgetRepository(db_session)

    cc = CostCenter(code=CostCenterCode("6.1"), name="Human Resources")
    await cc_repo.add(cc)

    target = BudgetTarget(
        cost_center_id=cc.id,
        period=Period.from_string("2026-04"),
        category="OPEX",
        amount=Money(Decimal("50000.00")),
    )
    await budget_repo.add(target)

    target.update_amount(Money(Decimal("60000.00")))
    target.category = "REVISED_OPEX"
    await budget_repo.update(target)

    updated = await budget_repo.get_by_id(target.id)
    assert updated is not None
    assert updated.amount == Money(Decimal("60000.00"))
    assert updated.category == "REVISED_OPEX"

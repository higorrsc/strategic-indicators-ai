"""Data Transfer Objects for budgeting application layer."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateCostCenterCommand:
    """Command payload to create a new Cost Center."""

    code: str
    name: str
    parent_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CostCenterDTO:
    """Output DTO representing a Cost Center."""

    id: UUID
    code: str
    name: str
    parent_id: UUID | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class SetBudgetTargetCommand:
    """Command payload to set a planned budget line."""

    cost_center_id: UUID
    period: str
    category: str
    amount: Decimal
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class BudgetTargetDTO:
    """Output DTO representing a planned budget line."""

    id: UUID
    cost_center_id: UUID
    period: str
    category: str
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class GetHierarchyBudgetQuery:
    """Query payload to fetch direct and consolidated hierarchical budgets."""

    cost_center_id: UUID
    period: str


@dataclass(frozen=True, slots=True)
class HierarchyBudgetDTO:
    """Output DTO containing direct and consolidated hierarchical budget figures."""

    cost_center_id: UUID
    cost_center_code: str
    period: str
    direct_total: Decimal
    consolidated_total: Decimal
    currency: str
    budget_lines: list[BudgetTargetDTO]

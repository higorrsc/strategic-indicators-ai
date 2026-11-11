from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateCostCenterCommand:
    code: str
    name: str
    parent_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CostCenterDTO:
    id: UUID
    code: str
    name: str
    parent_id: UUID | None
    is_active: bool


@dataclass(frozen=True, slots=True)
class SetBudgetTargetCommand:
    cost_center_id: UUID
    period: str
    category: str
    amount: Decimal
    currency: str = "USD"


@dataclass(frozen=True, slots=True)
class BudgetTargetDTO:
    id: UUID
    cost_center_id: UUID
    period: str
    category: str
    amount: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class GetHierarchyBudgetQuery:
    cost_center_id: UUID
    period: str


@dataclass(frozen=True, slots=True)
class HierarchyBudgetDTO:
    cost_center_id: UUID
    cost_center_code: str
    period: str
    direct_total: Decimal
    consolidated_total: Decimal
    currency: str
    budget_lines: list[BudgetTargetDTO]

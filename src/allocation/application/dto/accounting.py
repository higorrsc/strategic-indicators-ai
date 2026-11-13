"""Accounting DTOs for allocation application layer."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterAccountingAccountCommand:
    """Command payload to register an accounting account."""

    code: str
    name: str
    description: str = ""


@dataclass(frozen=True, slots=True)
class AccountingAccountDTO:
    """Output DTO representing an accounting account."""

    id: UUID
    code: str
    name: str
    description: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class ListAccountingAccountsQuery:
    """Query parameters to list accounting accounts."""

    active_only: bool = True
    page: int = 1
    per_page: int = 20


@dataclass(frozen=True, slots=True)
class CostCenterAccountSpendDTO:
    """DTO representing spend within a cost center for a specific accounting account."""

    accounting_account_id: UUID | None
    account_code: str | None
    account_name: str | None
    spent_amount: Decimal
    share_pct: Decimal


@dataclass(frozen=True, slots=True)
class CostCenterAccountingBreakdownDTO:
    """Output DTO representing a cost center's expenditures partitioned by account."""

    cost_center_id: UUID
    period: str
    total_spent: Decimal
    accounts: list[CostCenterAccountSpendDTO]

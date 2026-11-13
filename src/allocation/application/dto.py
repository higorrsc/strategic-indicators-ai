"""Data Transfer Objects for cost allocation application layer."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PaginatedResultDTO[T]:
    """Application DTO holding paginated slice items and total count."""

    items: list[T]
    total_items: int
    page: int
    per_page: int


@dataclass(frozen=True, slots=True)
class AllocationShareDTO:
    """DTO representing an allocation percentage share for a cost center."""

    cost_center_id: UUID
    percentage: Decimal
    accounting_account_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class AllocationEntryDTO:
    """DTO representing a calculated monetary allocation entry."""

    id: UUID
    cost_center_id: UUID
    amount: Decimal
    percentage: Decimal
    currency: str
    accounting_account_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class RegisterContractCommand:
    """Command payload to register a vendor contract."""

    code: str
    supplier_id: UUID
    title: str
    default_allocations: list[AllocationShareDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ContractDTO:
    """Output DTO representing a contract."""

    id: UUID
    code: str
    supplier_id: UUID
    title: str
    default_allocations: list[AllocationShareDTO]
    is_active: bool


@dataclass(frozen=True, slots=True)
class SubmitMeasurementCommand:
    """Command payload to submit a measurement expense."""

    contract_id: UUID
    period: str
    description: str
    gross_amount: Decimal
    currency: str = "USD"
    custom_allocations: list[AllocationShareDTO] | None = None


@dataclass(frozen=True, slots=True)
class MeasurementDTO:
    """Output DTO representing a financial measurement and its allocation lines."""

    id: UUID
    contract_id: UUID
    period: str
    description: str
    gross_amount: Decimal
    currency: str
    state: str
    entries: list[AllocationEntryDTO]


@dataclass(frozen=True, slots=True)
class ApproveMeasurementCommand:
    """Command payload to approve a measurement."""

    measurement_id: UUID


@dataclass(frozen=True, slots=True)
class ListContractsQuery:
    """Query parameters to filter contracts."""

    supplier_id: UUID | None = None
    active_only: bool = True
    page: int = 1
    per_page: int = 20


@dataclass(frozen=True, slots=True)
class ListMeasurementsQuery:
    """Query parameters to filter measurements."""

    period: str | None = None
    contract_id: UUID | None = None
    state: str | None = None
    page: int = 1
    per_page: int = 20


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


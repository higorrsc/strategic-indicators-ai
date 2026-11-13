"""Contract DTOs for allocation application layer."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AllocationShareDTO:
    """DTO representing an allocation percentage share for a cost center."""

    cost_center_id: UUID
    percentage: Decimal
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
class ListContractsQuery:
    """Query parameters to filter contracts."""

    supplier_id: UUID | None = None
    active_only: bool = True
    page: int = 1
    per_page: int = 20

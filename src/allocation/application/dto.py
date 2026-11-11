from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AllocationShareDTO:
    cost_center_id: UUID
    percentage: Decimal


@dataclass(frozen=True, slots=True)
class AllocationEntryDTO:
    id: UUID
    cost_center_id: UUID
    amount: Decimal
    percentage: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class RegisterContractCommand:
    code: str
    supplier_id: UUID
    title: str
    default_allocations: list[AllocationShareDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ContractDTO:
    id: UUID
    code: str
    supplier_id: UUID
    title: str
    default_allocations: list[AllocationShareDTO]
    is_active: bool


@dataclass(frozen=True, slots=True)
class SubmitMeasurementCommand:
    contract_id: UUID
    period: str
    description: str
    gross_amount: Decimal
    currency: str = "USD"
    custom_allocations: list[AllocationShareDTO] | None = None


@dataclass(frozen=True, slots=True)
class MeasurementDTO:
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
    measurement_id: UUID

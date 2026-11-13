"""Measurement DTOs for allocation application layer."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from .contract import AllocationShareDTO


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
class ListMeasurementsQuery:
    """Query parameters to filter measurements."""

    period: str | None = None
    contract_id: UUID | None = None
    state: str | None = None
    page: int = 1
    per_page: int = 20

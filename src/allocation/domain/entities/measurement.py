"""Measurement aggregate representing contract expenses and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID, uuid4

from src.allocation.domain.exceptions import (
    AllocationDomainError,
    AllocationReconciliationError,
    InvalidMeasurementStateError,
)
from src.shared.domain.value_objects import Money, Percentage, Period


class MeasurementState(StrEnum):
    """Lifecycle states for financial measurements."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class AllocationEntry:
    """Represents a finalized monetary allocation entry to a cost center."""

    cost_center_id: UUID
    amount: Money
    percentage: Percentage
    accounting_account_id: UUID | None = None
    id: UUID = field(default_factory=uuid4)


@dataclass(slots=True)
class Measurement:
    """Aggregate representing a contract expense and its cost distribution."""

    contract_id: UUID
    period: Period
    description: str
    gross_amount: Money
    id: UUID = field(default_factory=uuid4)
    state: MeasurementState = MeasurementState.DRAFT
    entries: list[AllocationEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate measurement description and positive gross amount."""
        trimmed = self.description.strip()
        if not trimmed:
            raise AllocationDomainError("Measurement description cannot be empty.")
        self.description = trimmed
        if not self.gross_amount.is_positive():
            raise AllocationDomainError(
                f"Gross amount must be positive: {self.gross_amount.amount}."
            )

    def set_entries(self, entries: list[AllocationEntry]) -> None:
        """Assign allocation entries; permitted only while in DRAFT state.

        Args:
            entries: List of allocated entries.
        """
        if self.state != MeasurementState.DRAFT:
            raise InvalidMeasurementStateError(
                f"Cannot modify allocation in state '{self.state}'."
            )
        self.entries = list(entries)

    def _validate_entries_reconciliation(self) -> None:
        """Verify that sum of allocated lines matches gross amount."""
        if not self.entries:
            raise AllocationReconciliationError(
                "Measurement has no allocation entries."
            )
        total_allocated = sum(
            (entry.amount for entry in self.entries),
            Money.zero(self.gross_amount.currency),
        )
        if total_allocated != self.gross_amount:
            raise AllocationReconciliationError(
                f"Allocation sum {total_allocated.amount} "
                f"does not match gross amount {self.gross_amount.amount}."
            )

    def submit(self) -> None:
        """Submit draft measurement for approval verifying exact allocation closure."""
        if self.state != MeasurementState.DRAFT:
            raise InvalidMeasurementStateError(
                f"Only DRAFT measurements can be submitted; current: '{self.state}'."
            )
        self._validate_entries_reconciliation()
        self.state = MeasurementState.SUBMITTED

    def approve(self) -> None:
        """Approve submitted measurement, activating budget execution entries."""
        if self.state != MeasurementState.SUBMITTED:
            raise InvalidMeasurementStateError(
                f"Only SUBMITTED measurements can be approved; current: '{self.state}'."
            )
        self._validate_entries_reconciliation()
        self.state = MeasurementState.APPROVED

    def cancel(self) -> None:
        """Cancel measurement."""
        if self.state == MeasurementState.APPROVED:
            raise InvalidMeasurementStateError(
                "Approved measurements cannot be cancelled directly."
            )
        self.state = MeasurementState.CANCELLED

    def revert_to_draft(self) -> None:
        """Revert submitted measurement back to draft for correction."""
        if self.state != MeasurementState.SUBMITTED:
            raise InvalidMeasurementStateError(
                f"Only SUBMITTED measurements can be reverted; current: '{self.state}'."
            )
        self.state = MeasurementState.DRAFT

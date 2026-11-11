from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.allocation.domain.exceptions import AllocationDomainError


@dataclass(slots=True)
class Supplier:
    """Supplier entity representing a contracting third party vendor."""

    name: str
    tax_id: str
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        trimmed_name = self.name.strip()
        trimmed_tax_id = self.tax_id.strip()
        if not trimmed_name:
            raise AllocationDomainError("Supplier name cannot be empty.")
        if not trimmed_tax_id:
            raise AllocationDomainError("Supplier tax ID cannot be empty.")
        self.name = trimmed_name
        self.tax_id = trimmed_tax_id

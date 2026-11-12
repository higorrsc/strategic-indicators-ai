"""Domain models representing cost allocation anomalies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from src.shared.domain.value_objects import Percentage


class AnomalyType(StrEnum):
    """Classification types for cost allocation anomalies."""

    ABRUPT_ALLOCATION_SHIFT = "ABRUPT_ALLOCATION_SHIFT"
    POTENTIAL_BUDGET_DUMPING = "POTENTIAL_BUDGET_DUMPING"


class AnomalySeverity(StrEnum):
    """Risk severity levels for detected anomalies."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class AllocationAnomaly:
    """Represents an identified anomaly or suspicious pattern in a measurement."""

    measurement_id: UUID
    contract_id: UUID
    cost_center_id: UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    baseline_percentage: Percentage | None = None
    actual_percentage: Percentage | None = None

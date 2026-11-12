"""Domain service detecting cost allocation anomalies and potential budget dumping."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from src.allocation.domain.entities.measurement import (
    Measurement,
    MeasurementState,
)
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.intelligence.domain.models import (
    AllocationAnomaly,
    AnomalySeverity,
    AnomalyType,
)
from src.shared.domain.value_objects import Percentage

_DEFAULT_SHIFT_THRESHOLD = Decimal("25.00")


class AllocationAnomalyDetector:
    """Detects irregular allocation spikes, drift, and budget dumping patterns."""

    @classmethod
    def detect_abrupt_shifts(
        cls,
        current_measurement: Measurement,
        historical_measurements: list[Measurement],
        threshold_percentage: Decimal = _DEFAULT_SHIFT_THRESHOLD,
    ) -> list[AllocationAnomaly]:
        """Detect abrupt deviations from historical average allocation shares.

        Args:
            current_measurement: The measurement to evaluate.
            historical_measurements: Prior approved measurements for baseline context.
            threshold_percentage: Absolute percentage point shift to trigger an alert.

        Returns:
            list[AllocationAnomaly]: List of detected shift anomalies.
        """
        # Filter past approved measurements for the same contract
        contract_history = [
            m
            for m in historical_measurements
            if m.contract_id == current_measurement.contract_id
            and m.id != current_measurement.id
            and m.state == MeasurementState.APPROVED
        ]

        if not contract_history:
            return []

        # Calculate average historical share per cost center
        sums: dict[UUID, Decimal] = {}
        counts: dict[UUID, int] = {}
        for m in contract_history:
            for e in m.entries:
                sums[e.cost_center_id] = (
                    sums.get(e.cost_center_id, Decimal("0.00")) + e.percentage.value
                )
                counts[e.cost_center_id] = counts.get(e.cost_center_id, 0) + 1

        historical_avg: dict[UUID, Decimal] = {
            cc_id: sums[cc_id] / Decimal(str(len(contract_history))) for cc_id in sums
        }

        anomalies: list[AllocationAnomaly] = []

        for entry in current_measurement.entries:
            actual_pct = entry.percentage.value
            baseline_pct = historical_avg.get(entry.cost_center_id, Decimal("0.00"))
            delta = actual_pct - baseline_pct

            if delta >= threshold_percentage:
                severity = (
                    AnomalySeverity.HIGH
                    if delta >= Decimal("35.00")
                    or (
                        baseline_pct > Decimal("0.00")
                        and actual_pct >= baseline_pct * 3
                    )
                    else AnomalySeverity.MEDIUM
                )
                anomalies.append(
                    AllocationAnomaly(
                        measurement_id=current_measurement.id,
                        contract_id=current_measurement.contract_id,
                        cost_center_id=entry.cost_center_id,
                        anomaly_type=AnomalyType.ABRUPT_ALLOCATION_SHIFT,
                        severity=severity,
                        description=(
                            f"Allocation share spiked from historical average "
                            f"{baseline_pct:.2f}% to {actual_pct:.2f}% (+{delta:.2f}%)."
                        ),
                        baseline_percentage=Percentage.from_number(baseline_pct),
                        actual_percentage=entry.percentage,
                    )
                )

        return anomalies

    @classmethod
    def detect_budget_dumping(
        cls,
        measurement: Measurement,
        indicators: dict[UUID, CostCenterIndicator],
        contract_historical_measurements: list[Measurement] | None = None,
    ) -> list[AllocationAnomaly]:
        """Detect potential budget dumping to relieve pressure on over-budget centers.

        Args:
            measurement: Measurement to evaluate.
            indicators: Current indicator metrics mapped by cost_center_id.
            contract_historical_measurements: Prior measurements on this contract.

        Returns:
            list[AllocationAnomaly]: Identified potential dumping anomalies.
        """
        if not indicators or not measurement.entries:
            return []

        # Find if contract historically had major allocations to an overrun center
        overrun_centers = {
            cc_id
            for cc_id, ind in indicators.items()
            if ind.status == IndicatorStatus.CRITICAL_OVERRUN
        }

        if not overrun_centers:
            return []

        anomalies: list[AllocationAnomaly] = []
        for entry in measurement.entries:
            ind = indicators.get(entry.cost_center_id)
            if not ind:
                continue

            # If allocated to a healthy center, check if historically on overrun
            if (
                ind.status == IndicatorStatus.NORMAL
                and contract_historical_measurements
            ):
                for past in contract_historical_measurements:
                    if past.contract_id != measurement.contract_id:
                        continue
                    for past_e in past.entries:
                        if (
                            past_e.cost_center_id in overrun_centers
                            and past_e.percentage.value >= Decimal("40.00")
                            and entry.percentage.value >= Decimal("40.00")
                        ):
                            anomalies.append(
                                AllocationAnomaly(
                                    measurement_id=measurement.id,
                                    contract_id=measurement.contract_id,
                                    cost_center_id=entry.cost_center_id,
                                    anomaly_type=AnomalyType.POTENTIAL_BUDGET_DUMPING,
                                    severity=AnomalySeverity.HIGH,
                                    description=(
                                        f"High allocation ({entry.percentage.value}%) "
                                        f"assigned to healthy center "
                                        f"{ind.cost_center_code} on contract "
                                        f"historically borne by over-budget center."
                                    ),
                                    actual_percentage=entry.percentage,
                                )
                            )
                            break

        return anomalies

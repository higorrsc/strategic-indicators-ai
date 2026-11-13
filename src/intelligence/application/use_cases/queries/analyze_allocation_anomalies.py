"""Use case analyzing cost allocation anomalies and potential budget dumping."""

from __future__ import annotations

from uuid import UUID

from src.allocation.domain.exceptions import MeasurementNotFoundError
from src.allocation.domain.repositories import MeasurementRepository
from src.indicators.application.dto import ComputePeriodIndicatorsQuery
from src.indicators.application.use_cases.queries import (
    ComputePeriodIndicatorsUseCase,
)
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.intelligence.domain.models import AllocationAnomaly
from src.intelligence.domain.services.anomaly_detector import AllocationAnomalyDetector
from src.shared.domain.value_objects import Money, Percentage, Period


class AnalyzeAllocationAnomaliesUseCase:
    """Orchestrates anomaly detection across contract measurements and periods."""

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        indicators_use_case: ComputePeriodIndicatorsUseCase | None = None,
    ) -> None:
        """Initialize use case with required repositories and services.

        Args:
            measurement_repository: Persistence port for measurements.
            indicators_use_case: Optional use case for period indicators.
        """
        self._measurement_repository = measurement_repository
        self._indicators_use_case = indicators_use_case

    async def analyze_measurement(
        self, measurement_id: UUID
    ) -> list[AllocationAnomaly]:
        """Analyze a single measurement for allocation anomalies.

        Args:
            measurement_id: Unique identifier of the measurement to evaluate.

        Returns:
            list[AllocationAnomaly]: Detected anomalies.

        Raises:
            MeasurementNotFoundError: If the target measurement does not exist.
        """
        measurement = await self._measurement_repository.get_by_id(measurement_id)
        if not measurement:
            msg = f"Measurement '{measurement_id}' not found."
            raise MeasurementNotFoundError(msg)

        contract_history = await self._measurement_repository.list_by_contract(
            measurement.contract_id
        )

        indicators_map: dict[UUID, CostCenterIndicator] = {}
        if self._indicators_use_case:
            summary = await self._indicators_use_case.execute(
                ComputePeriodIndicatorsQuery(period=str(measurement.period))
            )
            indicators_map = {
                ind.cost_center_id: CostCenterIndicator(
                    cost_center_id=ind.cost_center_id,
                    cost_center_code=ind.cost_center_code,
                    period=measurement.period,
                    budgeted_amount=Money(ind.budgeted_amount, ind.currency),
                    actual_amount=Money(ind.actual_amount, ind.currency),
                    variance_amount=Money(ind.variance_amount, ind.currency),
                    execution_rate=Percentage.from_number(ind.execution_rate),
                    status=IndicatorStatus(ind.status),
                )
                for ind in summary.indicators
            }

        shift_anomalies = AllocationAnomalyDetector.detect_abrupt_shifts(
            current_measurement=measurement,
            historical_measurements=contract_history,
        )
        dumping_anomalies = AllocationAnomalyDetector.detect_budget_dumping(
            measurement=measurement,
            indicators=indicators_map,
            contract_historical_measurements=contract_history,
        )

        return [*shift_anomalies, *dumping_anomalies]

    async def analyze_period(self, period: Period) -> list[AllocationAnomaly]:
        """Analyze all measurements submitted or approved within a period.

        Args:
            period: Fiscal period to inspect.

        Returns:
            list[AllocationAnomaly]: Aggregated anomalies for the entire period.
        """
        measurements = await self._measurement_repository.list_by_period(period)
        if not measurements:
            return []

        indicators_map: dict[UUID, CostCenterIndicator] = {}
        if self._indicators_use_case:
            summary = await self._indicators_use_case.execute(
                ComputePeriodIndicatorsQuery(period=str(period))
            )
            indicators_map = {
                ind.cost_center_id: CostCenterIndicator(
                    cost_center_id=ind.cost_center_id,
                    cost_center_code=ind.cost_center_code,
                    period=period,
                    budgeted_amount=Money(ind.budgeted_amount, ind.currency),
                    actual_amount=Money(ind.actual_amount, ind.currency),
                    variance_amount=Money(ind.variance_amount, ind.currency),
                    execution_rate=Percentage.from_number(ind.execution_rate),
                    status=IndicatorStatus(ind.status),
                )
                for ind in summary.indicators
            }

        anomalies: list[AllocationAnomaly] = []
        for m in measurements:
            contract_history = await self._measurement_repository.list_by_contract(
                m.contract_id
            )
            shifts = AllocationAnomalyDetector.detect_abrupt_shifts(
                current_measurement=m,
                historical_measurements=contract_history,
            )
            dumping = AllocationAnomalyDetector.detect_budget_dumping(
                measurement=m,
                indicators=indicators_map,
                contract_historical_measurements=contract_history,
            )
            anomalies.extend(shifts)
            anomalies.extend(dumping)

        return anomalies

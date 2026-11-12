"""Use case generating executive summary and strategic insights for a period."""

from __future__ import annotations

from src.indicators.application.dto import ComputePeriodIndicatorsQuery
from src.indicators.application.use_cases import ComputePeriodIndicatorsUseCase
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.intelligence.application.dto import AnomalyDTO, ExecutiveSummaryDTO
from src.intelligence.application.ports.ai_port import AIPort
from src.intelligence.application.use_cases.analyze_allocation_anomalies import (
    AnalyzeAllocationAnomaliesUseCase,
)
from src.intelligence.domain.exceptions import AIProviderError
from src.shared.config.settings import Settings, get_settings
from src.shared.domain.value_objects import Money, Percentage, Period


class GenerateExecutiveSummaryUseCase:
    """Coordinates deterministic indicator calculation, anomaly detection, and AI."""

    def __init__(
        self,
        indicators_use_case: ComputePeriodIndicatorsUseCase,
        anomalies_use_case: AnalyzeAllocationAnomaliesUseCase,
        ai_port: AIPort,
        settings: Settings | None = None,
    ) -> None:
        """Initialize use case with indicators, anomaly detector, and AI port.

        Args:
            indicators_use_case: Use case computing planned vs actual variance.
            anomalies_use_case: Use case detecting allocation anomalies.
            ai_port: Application port for AI model interactions.
            settings: Application configuration settings.
        """
        self._indicators_use_case = indicators_use_case
        self._anomalies_use_case = anomalies_use_case
        self._ai_port = ai_port
        self._settings = settings or get_settings()

    async def execute(self, period: Period) -> ExecutiveSummaryDTO:
        """Generate comprehensive executive report for the given period.

        Args:
            period: Target fiscal period.

        Returns:
            ExecutiveSummaryDTO: Consolidated report with deterministic and AI insights.
        """
        indicators_summary = await self._indicators_use_case.execute(
            ComputePeriodIndicatorsQuery(period=str(period))
        )
        domain_indicators = [
            CostCenterIndicator(
                cost_center_id=ind.cost_center_id,
                cost_center_code=ind.cost_center_code,
                period=period,
                budgeted_amount=Money(ind.budgeted_amount, ind.currency),
                actual_amount=Money(ind.actual_amount, ind.currency),
                variance_amount=Money(ind.variance_amount, ind.currency),
                execution_rate=Percentage.from_number(ind.execution_rate),
                status=IndicatorStatus(ind.status),
            )
            for ind in indicators_summary.indicators
        ]
        domain_anomalies = await self._anomalies_use_case.analyze_period(period)
        anomaly_dtos = [AnomalyDTO.from_domain(a) for a in domain_anomalies]

        try:
            ai_response = await self._ai_port.generate_executive_summary(
                indicators=domain_indicators,
                anomalies=domain_anomalies,
                period=period,
            )
            return ExecutiveSummaryDTO(
                period=period,
                financial_health_status=ai_response.financial_health_status,
                executive_summary=ai_response.executive_summary,
                root_causes=ai_response.root_causes,
                strategic_recommendations=ai_response.strategic_recommendations,
                anomalies=anomaly_dtos,
                indicators_summary=indicators_summary,
                is_fallback=False,
                ai_provider=self._settings.AI_PROVIDER,
            )
        except AIProviderError as err:
            import logging

            logging.getLogger(__name__).warning(
                "AI provider failed, falling back: %s", err
            )
            # Deterministic graceful degradation without crashing financial delivery
            overruns = [
                i
                for i in indicators_summary.indicators
                if i.status != IndicatorStatus.NORMAL.value
            ]
            root_causes = [
                f"Cost center {i.cost_center_code} exceeded threshold: "
                f"execution rate {i.execution_rate}%."
                for i in overruns
            ]
            if domain_anomalies:
                root_causes.extend(
                    f"{a.anomaly_type.value}: {a.description}" for a in domain_anomalies
                )
            if not root_causes:
                root_causes.append("All cost centers operated within budget limits.")

            summary_text = (
                f"Executive report for period {period} generated via "
                f"deterministic fallback.\n"
                f"Planned: {indicators_summary.total_budgeted}, "
                f"Actual: {indicators_summary.total_actual}, "
                f"Variance: {indicators_summary.total_variance}."
            )

            return ExecutiveSummaryDTO(
                period=period,
                financial_health_status="UNAVAILABLE (AI FALLBACK)",
                executive_summary=summary_text,
                root_causes=root_causes,
                strategic_recommendations=[
                    "Conduct operational audit of over-budget cost centers.",
                    "Review flagged cost allocation shifts.",
                ],
                anomalies=anomaly_dtos,
                indicators_summary=indicators_summary,
                is_fallback=True,
                ai_provider=self._settings.AI_PROVIDER,
            )

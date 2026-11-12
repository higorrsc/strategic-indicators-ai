"""Deterministic in-memory fake implementation of AIPort for testing."""

from __future__ import annotations

from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.indicators.domain.services.simulator import CostCenterImpact
from src.intelligence.application.ports.ai_port import (
    AIPort,
    ExecutiveSummaryResponse,
    ScenarioEvaluationResponse,
)
from src.intelligence.domain.models import AllocationAnomaly
from src.shared.domain.value_objects import Period


class FakeAIPort(AIPort):
    """Deterministic in-memory AI adapter producing structured responses."""

    def __init__(
        self,
        canned_summary: ExecutiveSummaryResponse | None = None,
        canned_scenario: ScenarioEvaluationResponse | None = None,
    ) -> None:
        """Initialize fake AI port with optional canned fixtures.

        Args:
            canned_summary: Optional predetermined summary response.
            canned_scenario: Optional predetermined scenario response.
        """
        self._canned_summary = canned_summary
        self._canned_scenario = canned_scenario

    async def generate_executive_summary(
        self,
        indicators: list[CostCenterIndicator],
        anomalies: list[AllocationAnomaly],
        period: Period,
    ) -> ExecutiveSummaryResponse:
        """Generate deterministic executive summary from indicators and anomalies.

        Args:
            indicators: Cost center indicators.
            anomalies: Detected anomalies.
            period: Target period.

        Returns:
            ExecutiveSummaryResponse: Synthesized executive report.
        """
        if self._canned_summary:
            return self._canned_summary

        overrun_centers = [
            ind.cost_center_code
            for ind in indicators
            if ind.status == IndicatorStatus.CRITICAL_OVERRUN
        ]

        if overrun_centers:
            health = "CRITICAL"
            summary = (
                f"Fiscal period {period} experienced critical budgetary overruns "
                f"concentrated in cost center(s): {', '.join(overrun_centers)}."
            )
        elif anomalies:
            health = "CONCERNING"
            summary = (
                f"Fiscal period {period} is within global targets but has "
                f"{len(anomalies)} suspicious allocation anomalies requiring audit."
            )
        else:
            health = "HEALTHY"
            summary = (
                f"Fiscal period {period} closed with balanced budget execution "
                f"across all monitored departments."
            )

        root_causes = [
            f"Cost center {code} exceeded budget limits." for code in overrun_centers
        ]
        for a in anomalies:
            root_causes.append(f"{a.anomaly_type}: {a.description}")

        if not root_causes:
            root_causes.append(
                "All departmental expenditure conformed to planned targets."
            )

        recommendations = (
            [
                "Initiate immediate review of vendor contract consumption.",
                "Enforce allocation freeze on over-budget units.",
            ]
            if overrun_centers
            else ["Maintain current operational budget allocation guidelines."]
        )

        return ExecutiveSummaryResponse(
            executive_summary=summary,
            financial_health_status=health,
            root_causes=root_causes,
            strategic_recommendations=recommendations,
        )

    async def evaluate_scenario(
        self,
        scenario_name: str,
        impacts: list[CostCenterImpact],
        period: Period,
    ) -> ScenarioEvaluationResponse:
        """Generate deterministic scenario appraisal.

        Args:
            scenario_name: Name of the scenario.
            impacts: Differential impacts.
            period: Target period.

        Returns:
            ScenarioEvaluationResponse: Evaluated scenario appraisal.
        """
        if self._canned_scenario:
            return self._canned_scenario

        new_overruns = [imp.cost_center_code for imp in impacts if imp.new_overrun]

        if new_overruns:
            feasibility = "LOW"
            tradeoffs = [
                f"Causes new budget overruns in: {', '.join(new_overruns)}.",
                "Increases global financial commitments without offsetting savings.",
            ]
            recommendations = [
                "Reject scenario or negotiate tiered vendor volume discounts.",
                "Rebalance allocation proportions to avoid departmental deficits.",
            ]
        else:
            feasibility = "HIGH"
            tradeoffs = ["Adjustments remain within departmental contingency margins."]
            recommendations = [
                "Proceed with scenario planning and communicate modified allocations."
            ]

        return ScenarioEvaluationResponse(
            scenario_name=scenario_name,
            strategic_feasibility=feasibility,
            key_tradeoffs=tradeoffs,
            recommendations=recommendations,
        )

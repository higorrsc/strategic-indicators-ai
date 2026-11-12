"""Pydantic AI infrastructure adapter supporting local Ollama, Google, and OpenAI."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.providers.openai import OpenAIProvider

from src.indicators.domain.models import CostCenterIndicator
from src.indicators.domain.services.simulator import CostCenterImpact
from src.intelligence.application.ports.ai_port import (
    AIPort,
    ExecutiveSummaryResponse,
    ScenarioEvaluationResponse,
)
from src.intelligence.domain.exceptions import AIProviderError
from src.intelligence.domain.models import AllocationAnomaly
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIPort
from src.shared.config.settings import Settings, get_settings
from src.shared.domain.value_objects import Period


class PydanticAIAdapter(AIPort):
    """AI adapter integrating Pydantic AI for multi-provider executive insights."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize adapter with configured AI provider.

        Args:
            settings: Optional application settings. Defaults to singleton settings.
        """
        self._settings = settings or get_settings()
        self._fake_port = FakeAIPort() if self._settings.AI_PROVIDER == "fake" else None

        self._summary_agent: Agent[None, ExecutiveSummaryResponse] | None = None
        self._scenario_agent: Agent[None, ScenarioEvaluationResponse] | None = None

        if not self._fake_port:
            model = self._build_model()
            self._summary_agent = Agent(
                model=model,
                name="executive_summary_agent",
                output_type=ExecutiveSummaryResponse,
                retries=3,
                instructions=(
                    "You are a senior financial analyst and executive advisor. "
                    "Analyze organizational budget performance indicators, variance "
                    "thresholds, and detected cost allocation anomalies. Produce an "
                    "executive synthesis highlighting financial health, critical root "
                    "causes, and actionable strategic recommendations. "
                    "Always output valid JSON strictly conforming to "
                    "ExecutiveSummaryResponse."
                ),
            )
            self._scenario_agent = Agent(
                model=model,
                name="scenario_evaluation_agent",
                output_type=ScenarioEvaluationResponse,
                retries=3,
                instructions=(
                    "You are a strategic finance advisor. Evaluate the results of a "
                    "what-if budget simulation across cost centers. Assess strategic "
                    "feasibility, identify key operational trade-offs, and recommend "
                    "actions. Always output valid JSON strictly conforming to "
                    "ScenarioEvaluationResponse."
                ),
            )

    def _build_model(self) -> str | Model[Any]:
        """Resolve and instantiate the configured Pydantic AI model.

        Returns:
            str | Model[Any]: Resolved model identifier or instance.
        """
        provider = self._settings.AI_PROVIDER
        model_name = self._settings.AI_MODEL

        if provider == "ollama":
            ollama_provider = OllamaProvider(
                base_url=self._settings.AI_BASE_URL,
                api_key=self._settings.AI_API_KEY or "ollama",
            )
            return OllamaModel(model_name, provider=ollama_provider)

        if provider == "openai":
            api_key = (
                self._settings.AI_API_KEY
                or os.getenv("OPENAI_API_KEY")
                or "placeholder-key"
            )
            base_url = (
                self._settings.AI_BASE_URL
                if self._settings.AI_BASE_URL != "http://localhost:11434/v1"
                else None
            )
            openai_provider = OpenAIProvider(base_url=base_url, api_key=api_key)
            return OpenAIChatModel(model_name, provider=openai_provider)

        if provider == "google":
            api_key = (
                self._settings.AI_API_KEY
                or os.getenv("GOOGLE_API_KEY")
                or os.getenv("GEMINI_API_KEY")
                or "placeholder-key"
            )
            google_provider = GoogleProvider(api_key=api_key)
            return GoogleModel(model_name, provider=google_provider)

        return f"openai:{model_name}"

    async def generate_executive_summary(
        self,
        indicators: list[CostCenterIndicator],
        anomalies: list[AllocationAnomaly],
        period: Period,
    ) -> ExecutiveSummaryResponse:
        """Synthesize period metrics and anomalies into an executive summary.

        Args:
            indicators: Calculated performance indicators.
            anomalies: Detected allocation anomalies.
            period: The target fiscal period.

        Returns:
            ExecutiveSummaryResponse: Validated executive report.

        Raises:
            AIProviderError: If the AI provider fails or times out.
        """
        if self._fake_port:
            return await self._fake_port.generate_executive_summary(
                indicators, anomalies, period
            )

        if not self._summary_agent:
            msg = "Summary agent is not initialized."
            raise AIProviderError(msg)

        prompt = (
            f"Period: {period}\n\n"
            f"Indicators Summary:\n"
            + "\n".join(
                f"- Cost Center {i.cost_center_code}: "
                f"Planned={i.budgeted_amount.amount} {i.budgeted_amount.currency}, "
                f"Actual={i.actual_amount.amount} {i.actual_amount.currency}, "
                f"Variance={i.variance_amount.amount} {i.variance_amount.currency} "
                f"({float(i.execution_rate.value):.1f}%), Status={i.status.value}"
                for i in indicators
            )
            + "\n\nDetected Anomalies:\n"
            + (
                "\n".join(
                    f"- [{a.severity.value}] {a.anomaly_type.value}: {a.description}"
                    for a in anomalies
                )
                if anomalies
                else "None"
            )
        )

        try:
            result = await asyncio.wait_for(
                self._summary_agent.run(prompt),
                timeout=self._settings.AI_TIMEOUT_SECONDS,
            )
            return result.output
        except Exception as exc:
            msg = f"AI Provider '{self._settings.AI_PROVIDER}' failed: {exc}"
            raise AIProviderError(msg) from exc

    async def evaluate_scenario(
        self,
        scenario_name: str,
        impacts: list[CostCenterImpact],
        period: Period,
    ) -> ScenarioEvaluationResponse:
        """Evaluate strategic implications of a what-if simulation.

        Args:
            scenario_name: Name of the scenario.
            impacts: Differential impacts across cost centers.
            period: The evaluated period.

        Returns:
            ScenarioEvaluationResponse: Strategic feasibility analysis.

        Raises:
            AIProviderError: If the AI provider fails or times out.
        """
        if self._fake_port:
            return await self._fake_port.evaluate_scenario(
                scenario_name, impacts, period
            )

        if not self._scenario_agent:
            msg = "Scenario agent is not initialized."
            raise AIProviderError(msg)

        prompt = (
            f"Scenario: {scenario_name}\n"
            f"Period: {period}\n\n"
            f"Cost Center Impacts:\n"
            + "\n".join(
                f"- Cost Center {imp.cost_center_code}: "
                f"Baseline={imp.baseline_actual.amount} "
                f"{imp.baseline_actual.currency}, "
                f"Simulated={imp.simulated_actual.amount} "
                f"{imp.simulated_actual.currency}, "
                f"Delta={imp.delta_actual.amount} "
                f"{imp.delta_actual.currency}, "
                f"Baseline Status={imp.baseline_status.value}, "
                f"Simulated Status={imp.simulated_status.value}, "
                f"New Overrun={imp.new_overrun}"
                for imp in impacts
            )
        )

        try:
            result = await asyncio.wait_for(
                self._scenario_agent.run(prompt),
                timeout=self._settings.AI_TIMEOUT_SECONDS,
            )
            return result.output
        except Exception as exc:
            msg = f"AI Provider '{self._settings.AI_PROVIDER}' failed: {exc}"
            raise AIProviderError(msg) from exc

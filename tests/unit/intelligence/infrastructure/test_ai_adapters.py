from decimal import Decimal
from uuid import uuid4

import pytest

from src.indicators.domain.models import (
    CostCenterIndicator,
    IndicatorStatus,
)
from src.indicators.domain.services.simulator import CostCenterImpact
from src.intelligence.application.ports.ai_port import (
    ExecutiveSummaryResponse,
)
from src.intelligence.domain.exceptions import AIProviderError
from src.intelligence.domain.models import (
    AllocationAnomaly,
)
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIPort
from src.intelligence.infrastructure.pydantic_ai_adapter import PydanticAIAdapter
from src.shared.config.settings import Settings
from src.shared.domain.value_objects import (
    Money,
    Percentage,
    Period,
    SupportedLanguage,
)


class FailingAIPort(FakeAIPort):
    """Test double that simulates AI provider failure or timeout."""

    async def generate_executive_summary(
        self,
        indicators: list[CostCenterIndicator],
        anomalies: list[AllocationAnomaly],
        period: Period,
        language: SupportedLanguage = SupportedLanguage.PT_BR,
    ) -> ExecutiveSummaryResponse:
        msg = "LLM gateway timeout after 30 seconds."
        raise AIProviderError(msg)


@pytest.mark.asyncio
async def test_should_generate_fake_ai_summary_for_healthy_period() -> None:
    fake_ai = FakeAIPort()
    period = Period(2026, 3)
    indicator = CostCenterIndicator(
        cost_center_id=uuid4(),
        cost_center_code="CC-ENG",
        period=period,
        budgeted_amount=Money(Decimal("10000.00")),
        actual_amount=Money(Decimal("8000.00")),
        variance_amount=Money(Decimal("2000.00")),
        execution_rate=Percentage.from_number(Decimal("80.00")),
        status=IndicatorStatus.NORMAL,
    )

    response = await fake_ai.generate_executive_summary(
        indicators=[indicator],
        anomalies=[],
        period=period,
        language=SupportedLanguage.PT_BR,
    )

    assert response.financial_health_status == "HEALTHY"
    assert "2026-03" in response.executive_summary
    assert len(response.strategic_recommendations) >= 1


@pytest.mark.asyncio
async def test_should_generate_fake_ai_summary_for_critical_period() -> None:
    fake_ai = FakeAIPort()
    period = Period(2026, 3)
    indicator = CostCenterIndicator(
        cost_center_id=uuid4(),
        cost_center_code="CC-OPS",
        period=period,
        budgeted_amount=Money(Decimal("10000.00")),
        actual_amount=Money(Decimal("15000.00")),
        variance_amount=Money(Decimal("-5000.00")),
        execution_rate=Percentage.from_number(Decimal("150.00")),
        status=IndicatorStatus.CRITICAL_OVERRUN,
    )

    response_pt = await fake_ai.generate_executive_summary(
        indicators=[indicator],
        anomalies=[],
        period=period,
        language=SupportedLanguage.PT_BR,
    )
    assert response_pt.financial_health_status == "CRITICAL"
    assert "CC-OPS" in response_pt.executive_summary
    assert any("CC-OPS" in r for r in response_pt.root_causes)

    response_en = await fake_ai.generate_executive_summary(
        indicators=[indicator],
        anomalies=[],
        period=period,
        language=SupportedLanguage.EN_US,
    )
    assert response_en.financial_health_status == "CRITICAL"
    assert "CC-OPS" in response_en.executive_summary
    assert any("CC-OPS" in r for r in response_en.root_causes)


@pytest.mark.asyncio
async def test_should_evaluate_scenario_with_fake_ai() -> None:
    fake_ai = FakeAIPort()
    period = Period(2026, 3)
    impact = CostCenterImpact(
        cost_center_id=uuid4(),
        cost_center_code="CC-IT",
        baseline_actual=Money(Decimal("1000.00")),
        simulated_actual=Money(Decimal("1500.00")),
        delta_actual=Money(Decimal("500.00")),
        baseline_status=IndicatorStatus.NORMAL,
        simulated_status=IndicatorStatus.WARNING,
        new_overrun=False,
    )

    eval_resp = await fake_ai.evaluate_scenario(
        scenario_name="50% IT Inflation",
        impacts=[impact],
        period=period,
    )

    assert eval_resp.scenario_name == "50% IT Inflation"
    assert eval_resp.strategic_feasibility in {"HIGH", "MODERATE", "LOW"}
    assert len(eval_resp.key_tradeoffs) >= 1


def test_should_configure_pydantic_ai_adapter_with_different_providers() -> None:
    fake_settings = Settings(AI_PROVIDER="fake")
    adapter_fake = PydanticAIAdapter(settings=fake_settings)
    assert adapter_fake._fake_port is not None

    ollama_settings = Settings(
        AI_PROVIDER="ollama",
        AI_MODEL="llama3.2",
        AI_BASE_URL="http://localhost:11434/v1",
    )
    adapter_ollama = PydanticAIAdapter(settings=ollama_settings)
    assert adapter_ollama._summary_agent is not None

    google_settings = Settings(
        AI_PROVIDER="google",
        AI_MODEL="gemini-2.0-flash",
        AI_API_KEY="test-google-key",
    )
    adapter_google = PydanticAIAdapter(settings=google_settings)
    assert adapter_google._summary_agent is not None

    openai_settings = Settings(
        AI_PROVIDER="openai",
        AI_MODEL="gpt-4o",
        AI_API_KEY="test-openai-key",
    )
    adapter_openai = PydanticAIAdapter(settings=openai_settings)
    assert adapter_openai._summary_agent is not None

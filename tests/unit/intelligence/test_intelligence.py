"""Unit tests for the Strategic Intelligence bounded context."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.domain.entities.contract import Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.exceptions import MeasurementNotFoundError
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)
from src.indicators.application.use_cases import ComputePeriodIndicatorsUseCase
from src.indicators.domain.models import (
    CostCenterIndicator,
    IndicatorStatus,
)
from src.indicators.domain.services.simulator import CostCenterImpact
from src.intelligence.application.ports.ai_port import (
    ExecutiveSummaryResponse,
)
from src.intelligence.application.use_cases import (
    AnalyzeAllocationAnomaliesUseCase,
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.domain.exceptions import AIProviderError
from src.intelligence.domain.models import (
    AllocationAnomaly,
    AnomalySeverity,
    AnomalyType,
)
from src.intelligence.domain.services.anomaly_detector import (
    AllocationAnomalyDetector,
)
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIPort
from src.intelligence.infrastructure.pydantic_ai_adapter import PydanticAIAdapter
from src.shared.config.settings import Settings
from src.shared.domain.value_objects import (
    CostCenterCode,
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
        """Simulate an AI provider failure.

        Args:
            indicators: Input indicators.
            anomalies: Input anomalies.
            period: Target period.

        Raises:
            AIProviderError: Always raises to simulate failure.
        """
        msg = "LLM gateway timeout after 30 seconds."
        raise AIProviderError(msg)


# --- Anomaly Detector Tests ---


def test_should_detect_abrupt_allocation_percentage_shift() -> None:
    """Validate detection of sudden allocation shift against historical baseline."""
    contract_id = uuid4()
    cc_a = uuid4()
    cc_b = uuid4()
    period_jan = Period(2026, 1)
    period_feb = Period(2026, 2)
    period_mar = Period(2026, 3)

    # History: cc_a averaged 5%, cc_b averaged 95%
    past_1 = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_jan,
        description="January Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("5.00")),
                amount=Money(Decimal("500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("95.00")),
                amount=Money(Decimal("9500.00")),
            ),
        ],
    )
    past_2 = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_feb,
        description="February Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("5.00")),
                amount=Money(Decimal("500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("95.00")),
                amount=Money(Decimal("9500.00")),
            ),
        ],
    )

    # Current: cc_a suddenly jumps to 45%
    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_mar,
        description="March Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("45.00")),
                amount=Money(Decimal("4500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("55.00")),
                amount=Money(Decimal("5500.00")),
            ),
        ],
    )

    anomalies = AllocationAnomalyDetector.detect_abrupt_shifts(
        current_measurement=current,
        historical_measurements=[past_1, past_2],
    )

    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.anomaly_type == AnomalyType.ABRUPT_ALLOCATION_SHIFT
    assert anomaly.severity == AnomalySeverity.HIGH
    assert anomaly.cost_center_id == cc_a
    assert anomaly.baseline_percentage == Percentage.from_number(Decimal("5.00"))
    assert anomaly.actual_percentage == Percentage.from_number(Decimal("45.00"))
    assert "Allocation share spiked" in anomaly.description


def test_should_not_detect_shift_when_variation_is_within_threshold() -> None:
    """Verify that shifts below threshold do not trigger false anomalies."""
    contract_id = uuid4()
    cc_a = uuid4()
    period_jan = Period(2026, 1)
    period_feb = Period(2026, 2)

    past = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_jan,
        description="January Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("50.00")),
                amount=Money(Decimal("5000.00")),
            ),
        ],
    )
    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_feb,
        description="February Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("60.00")),
                amount=Money(Decimal("6000.00")),
            ),
        ],
    )

    anomalies = AllocationAnomalyDetector.detect_abrupt_shifts(
        current_measurement=current,
        historical_measurements=[past],
    )

    assert anomalies == []


def test_should_detect_budget_dumping_to_relieve_overrun_center() -> None:
    """Detect dumping when allocation shifts to healthy center from critical center."""
    contract_id = uuid4()
    overrun_cc_id = uuid4()
    healthy_cc_id = uuid4()
    period = Period(2026, 3)

    past = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=Period(2026, 2),
        description="Past Month Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=overrun_cc_id,
                percentage=Percentage.from_number(Decimal("80.00")),
                amount=Money(Decimal("8000.00")),
            ),
        ],
    )

    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period,
        description="Current Month Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=healthy_cc_id,
                percentage=Percentage.from_number(Decimal("80.00")),
                amount=Money(Decimal("8000.00")),
            ),
        ],
    )

    indicators = {
        overrun_cc_id: CostCenterIndicator(
            cost_center_id=overrun_cc_id,
            cost_center_code="CC-OVERRUN",
            period=period,
            budgeted_amount=Money(Decimal("1000.00")),
            actual_amount=Money(Decimal("5000.00")),
            variance_amount=Money(Decimal("-4000.00")),
            execution_rate=Percentage.from_number(Decimal("500.00")),
            status=IndicatorStatus.CRITICAL_OVERRUN,
        ),
        healthy_cc_id: CostCenterIndicator(
            cost_center_id=healthy_cc_id,
            cost_center_code="CC-HEALTHY",
            period=period,
            budgeted_amount=Money(Decimal("10000.00")),
            actual_amount=Money(Decimal("2000.00")),
            variance_amount=Money(Decimal("8000.00")),
            execution_rate=Percentage.from_number(Decimal("20.00")),
            status=IndicatorStatus.NORMAL,
        ),
    }

    anomalies = AllocationAnomalyDetector.detect_budget_dumping(
        measurement=current,
        indicators=indicators,
        contract_historical_measurements=[past],
    )

    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.anomaly_type == AnomalyType.POTENTIAL_BUDGET_DUMPING
    assert anomaly.severity == AnomalySeverity.HIGH
    assert anomaly.cost_center_id == healthy_cc_id
    assert "healthy center" in anomaly.description


# --- Fake AIPort & Adapter Tests ---


@pytest.mark.asyncio
async def test_should_generate_fake_ai_summary_for_healthy_period() -> None:
    """Verify that fake AI port returns a healthy structured summary in PT and EN."""
    fake_ai = FakeAIPort()
    period = Period(2026, 3)

    # Default (PT-BR)
    response_pt = await fake_ai.generate_executive_summary(
        indicators=[],
        anomalies=[],
        period=period,
    )
    assert response_pt.financial_health_status == "HEALTHY"
    assert "execução orçamentária equilibrada" in response_pt.executive_summary
    assert len(response_pt.strategic_recommendations) >= 1

    # Explicit EN-US
    response_en = await fake_ai.generate_executive_summary(
        indicators=[],
        anomalies=[],
        period=period,
        language=SupportedLanguage.EN_US,
    )
    assert response_en.financial_health_status == "HEALTHY"
    assert "balanced budget execution" in response_en.executive_summary
    assert len(response_en.strategic_recommendations) >= 1


@pytest.mark.asyncio
async def test_should_generate_fake_ai_summary_for_critical_period() -> None:
    """Verify fake AI port flags critical health when overruns exist in PT and EN."""
    fake_ai = FakeAIPort()
    period = Period(2026, 3)
    indicator = CostCenterIndicator(
        cost_center_id=uuid4(),
        cost_center_code="CC-OPS",
        period=period,
        budgeted_amount=Money(Decimal("100.00")),
        actual_amount=Money(Decimal("250.00")),
        variance_amount=Money(Decimal("-150.00")),
        execution_rate=Percentage.from_number(Decimal("250.00")),
        status=IndicatorStatus.CRITICAL_OVERRUN,
    )

    # PT-BR
    response_pt = await fake_ai.generate_executive_summary(
        indicators=[indicator],
        anomalies=[],
        period=period,
        language=SupportedLanguage.PT_BR,
    )
    assert response_pt.financial_health_status == "CRITICAL"
    assert "CC-OPS" in response_pt.executive_summary
    assert any("CC-OPS" in r for r in response_pt.root_causes)

    # EN-US
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
    """Verify that scenario evaluation produces structured feasibility feedback."""
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
    """Verify initialization logic across Ollama, OpenAI, Google, and Fake."""
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


# --- Use Cases Tests ---


@pytest.mark.asyncio
async def test_should_analyze_measurement_and_raise_if_not_found() -> None:
    """Ensure analyze measurement raises MeasurementNotFoundError for unknown ID."""
    measurement_repo = InMemoryMeasurementRepository()
    use_case = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo
    )

    with pytest.raises(MeasurementNotFoundError):
        await use_case.analyze_measurement(uuid4())


@pytest.mark.asyncio
async def test_should_generate_executive_summary_happy_path() -> None:
    """Verify end-to-end execution of GenerateExecutiveSummaryUseCase."""
    cost_center_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()

    period = Period(2026, 3)
    cc_id = uuid4()
    contract_id = uuid4()

    # Setup cost center
    await cost_center_repo.add(
        CostCenter(
            id=cc_id,
            code=CostCenterCode("1.1"),
            name="Technology",
        )
    )

    # Setup budget target
    await budget_repo.add(
        BudgetTarget(
            id=uuid4(),
            cost_center_id=cc_id,
            period=period,
            category="OPEX",
            amount=Money(Decimal("5000.00")),
        )
    )

    # Setup contract
    await contract_repo.add(
        Contract(
            id=contract_id,
            code="CTR-2026-001",
            supplier_id=uuid4(),
            title="Cloud Services",
        )
    )

    # Setup approved measurement
    await measurement_repo.add(
        Measurement(
            id=uuid4(),
            contract_id=contract_id,
            period=period,
            description="March Cloud Services",
            gross_amount=Money(Decimal("4000.00")),
            state=MeasurementState.APPROVED,
            entries=[
                AllocationEntry(
                    cost_center_id=cc_id,
                    percentage=Percentage.from_number(Decimal("100.00")),
                    amount=Money(Decimal("4000.00")),
                ),
            ],
        )
    )

    indicators_uc = ComputePeriodIndicatorsUseCase(
        cost_center_repository=cost_center_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )
    anomalies_uc = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo,
        indicators_use_case=indicators_uc,
    )
    fake_ai = FakeAIPort()

    summary_uc = GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_uc,
        anomalies_use_case=anomalies_uc,
        ai_port=fake_ai,
    )

    result = await summary_uc.execute(period)

    assert result.period == period
    assert not result.is_fallback
    assert result.language == SupportedLanguage.PT_BR
    assert result.financial_health_status in {
        "HEALTHY",
        "CONCERNING",
        "CRITICAL",
        "SAUDÁVEL",
        "ATENÇÃO",
        "CRÍTICO",
    }
    assert result.indicators_summary.total_budgeted == Decimal("5000.00")
    assert result.indicators_summary.total_actual == Decimal("4000.00")

    result_en = await summary_uc.execute(period, language=SupportedLanguage.EN_US)
    assert result_en.language == SupportedLanguage.EN_US
    assert result_en.financial_health_status in {
        "HEALTHY",
        "CONCERNING",
        "CRITICAL",
    }


@pytest.mark.asyncio
async def test_should_gracefully_fallback_when_ai_provider_fails() -> None:
    """Verify fallback behavior preserves deterministic indicators on AI failure."""
    cost_center_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    measurement_repo = InMemoryMeasurementRepository()

    period = Period(2026, 3)

    indicators_uc = ComputePeriodIndicatorsUseCase(
        cost_center_repository=cost_center_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )
    anomalies_uc = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo,
        indicators_use_case=indicators_uc,
    )
    failing_ai = FailingAIPort()

    summary_uc = GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_uc,
        anomalies_use_case=anomalies_uc,
        ai_port=failing_ai,
    )

    # PT-BR fallback (default)
    result_pt = await summary_uc.execute(period)
    assert result_pt.is_fallback
    assert result_pt.language == SupportedLanguage.PT_BR
    assert "INDISPONÍVEL" in result_pt.financial_health_status
    assert "fallback determinístico" in result_pt.executive_summary
    assert len(result_pt.strategic_recommendations) >= 1

    # EN-US fallback
    result_en = await summary_uc.execute(period, language=SupportedLanguage.EN_US)
    assert result_en.is_fallback
    assert result_en.language == SupportedLanguage.EN_US
    assert "UNAVAILABLE" in result_en.financial_health_status
    assert "deterministic fallback" in result_en.executive_summary
    assert len(result_en.strategic_recommendations) >= 1

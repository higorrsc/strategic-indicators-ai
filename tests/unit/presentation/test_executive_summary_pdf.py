"""Unit tests for Executive Summary PDF generation."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.indicators.application.dto import (
    CostCenterIndicatorDTO,
    PeriodIndicatorsDTO,
)
from src.intelligence.application.dto import (
    AnomalyDTO,
    ExecutiveSummaryDTO,
)
from src.intelligence.domain.models import AnomalySeverity, AnomalyType
from src.presentation.reports.executive_summary_pdf import (
    ExecutiveSummaryPDFBuilder,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


def _sample_indicators() -> PeriodIndicatorsDTO:
    return PeriodIndicatorsDTO(
        period="2026-03",
        indicators=[
            CostCenterIndicatorDTO(
                cost_center_id=uuid4(),
                cost_center_code="1.0",
                period="2026-03",
                budgeted_amount=Decimal("100000.00"),
                actual_amount=Decimal("95000.00"),
                variance_amount=Decimal("-5000.00"),
                execution_rate=Decimal("95.00"),
                status="WARNING",
                currency="USD",
            ),
            CostCenterIndicatorDTO(
                cost_center_id=uuid4(),
                cost_center_code="1.1",
                period="2026-03",
                budgeted_amount=Decimal("150000.00"),
                actual_amount=Decimal("180000.00"),
                variance_amount=Decimal("30000.00"),
                execution_rate=Decimal("120.00"),
                status="CRITICAL_OVERRUN",
                currency="USD",
            ),
        ],
        total_budgeted=Decimal("250000.00"),
        total_actual=Decimal("275000.00"),
        total_variance=Decimal("25000.00"),
        total_execution_rate=Decimal("110.00"),
        currency="USD",
    )


def test_should_generate_pdf_with_valid_header_and_structure() -> None:
    builder = ExecutiveSummaryPDFBuilder()
    dto = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="CRITICAL_OVERRUN",
        executive_summary=(
            "Executive narrative highlighting high cloud computing expenditure."
        ),
        root_causes=["Unplanned compute capacity surge in March"],
        strategic_recommendations=["Renegotiate tiered AWS commitments"],
        anomalies=[
            AnomalyDTO(
                measurement_id=uuid4(),
                contract_id=uuid4(),
                cost_center_id=uuid4(),
                anomaly_type=AnomalyType.ABRUPT_ALLOCATION_SHIFT,
                severity=AnomalySeverity.HIGH,
                description="Allocation percentage shifted from 40% to 90%.",
            )
        ],
        indicators_summary=_sample_indicators(),
        is_fallback=False,
        ai_provider="ollama",
    )

    pdf_bytes = builder.build(dto)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000


def test_should_generate_pdf_without_anomalies_for_normal_status() -> None:
    builder = ExecutiveSummaryPDFBuilder()
    dto = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="NORMAL",
        executive_summary=(
            "All cost centers operating comfortably within planned targets."
        ),
        root_causes=[],
        strategic_recommendations=["Continue routine budget monitoring"],
        anomalies=[],
        indicators_summary=_sample_indicators(),
        is_fallback=False,
        ai_provider="google",
    )

    pdf_bytes = builder.build(dto)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1500


def test_should_sanitize_unicode_quotes_and_dashes_without_error() -> None:
    builder = ExecutiveSummaryPDFBuilder()
    dto = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="CRITICAL_OVERRUN",
        executive_summary=(
            "Analysis \u2014 highlighting \u201ccloud computing\u201d "
            "& IT costs \u2022 March 2026\u2026"
        ),
        root_causes=["Compute capacity surge \u2014 unforeseen spike"],
        strategic_recommendations=["Renegotiate commitments \u2018fast\u2019"],
        anomalies=[
            AnomalyDTO(
                measurement_id=uuid4(),
                contract_id=uuid4(),
                cost_center_id=uuid4(),
                anomaly_type=AnomalyType.ABRUPT_ALLOCATION_SHIFT,
                severity=AnomalySeverity.HIGH,
                description=(
                    "Allocation shift: 40% \u2192 90% \u201cabrupt change\u201d."
                ),
            )
        ],
        indicators_summary=_sample_indicators(),
        is_fallback=False,
        ai_provider="ollama",
    )

    pdf_bytes = builder.build(dto)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1500


def test_should_generate_pdf_with_fallback_advisory_banner() -> None:
    builder = ExecutiveSummaryPDFBuilder()
    dto = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="WARNING",
        executive_summary=(
            "Deterministic summary produced due to external LLM downtime."
        ),
        root_causes=["Cost center 1.0 approaching threshold limit"],
        strategic_recommendations=["Review monthly operational commitments"],
        anomalies=[],
        indicators_summary=_sample_indicators(),
        is_fallback=True,
        ai_provider="fallback",
    )

    pdf_bytes = builder.build(dto)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1500


def test_should_generate_pdf_in_portuguese_and_english() -> None:
    builder = ExecutiveSummaryPDFBuilder()
    dto_pt = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="CRITICAL_OVERRUN",
        executive_summary="Síntese executiva destacando estouro de custos em nuvem.",
        root_causes=["Aumento imprevisto de capacidade computacional em março."],
        strategic_recommendations=["Renegociar contratos escalonados da AWS."],
        anomalies=[],
        indicators_summary=_sample_indicators(),
        is_fallback=False,
        ai_provider="ollama",
        language=SupportedLanguage.PT_BR,
    )

    pdf_pt = builder.build(dto_pt)
    assert isinstance(pdf_pt, bytes)
    assert pdf_pt.startswith(b"%PDF")
    assert len(pdf_pt) > 1500

    dto_en = ExecutiveSummaryDTO(
        period=Period(2026, 3),
        financial_health_status="CRITICAL_OVERRUN",
        executive_summary="Executive synthesis highlighting cloud computing overruns.",
        root_causes=["Unplanned compute capacity surge in March."],
        strategic_recommendations=["Renegotiate tiered AWS commitments."],
        anomalies=[],
        indicators_summary=_sample_indicators(),
        is_fallback=False,
        ai_provider="ollama",
        language=SupportedLanguage.EN_US,
    )

    pdf_en = builder.build(dto_en)
    assert isinstance(pdf_en, bytes)
    assert pdf_en.startswith(b"%PDF")
    assert len(pdf_en) > 1500

    # Test language override parameter
    pdf_override = builder.build(dto_pt, language=SupportedLanguage.EN_US)
    assert isinstance(pdf_override, bytes)
    assert pdf_override.startswith(b"%PDF")

"""FastAPI router for Strategic Intelligence endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Response

from src.presentation.dependencies import (
    AnalyzeAnomaliesUseCaseDep,
    GenerateExecutiveSummaryUseCaseDep,
)
from src.presentation.reports.executive_summary_pdf import (
    ExecutiveSummaryPDFBuilder,
)
from src.presentation.schemas.indicators import (
    CostCenterIndicatorResponse,
    PeriodIndicatorsResponse,
)
from src.presentation.schemas.intelligence import (
    AnomalyResponse,
    ExecutiveSummaryResponseSchema,
)
from src.shared.domain.value_objects import Period

router = APIRouter(prefix="/api/v1/intelligence", tags=["Strategic Intelligence"])


@router.get(
    "/executive-summary",
    response_model=ExecutiveSummaryResponseSchema,
    summary="Generate executive summary and root causes for period",
)
async def get_executive_summary(
    period: Annotated[str, Query(description="Target period in YYYY-MM format")],
    use_case: GenerateExecutiveSummaryUseCaseDep,
) -> ExecutiveSummaryResponseSchema:
    """Synthesize period metrics and anomalies via AI with automatic fallback.

    Args:
        period: Target fiscal period string.
        use_case: GenerateExecutiveSummaryUseCase dependency.

    Returns:
        ExecutiveSummaryResponseSchema: Executive insights report.
    """
    target_period = Period.from_string(period)
    result = await use_case.execute(target_period)

    return ExecutiveSummaryResponseSchema(
        period=str(result.period),
        financial_health_status=result.financial_health_status,
        executive_summary=result.executive_summary,
        root_causes=result.root_causes,
        strategic_recommendations=result.strategic_recommendations,
        anomalies=[
            AnomalyResponse(
                measurement_id=a.measurement_id,
                contract_id=a.contract_id,
                cost_center_id=a.cost_center_id,
                anomaly_type=a.anomaly_type.value,
                severity=a.severity.value,
                description=a.description,
                baseline_percentage=a.baseline_percentage,
                actual_percentage=a.actual_percentage,
            )
            for a in result.anomalies
        ],
        indicators_summary=PeriodIndicatorsResponse(
            period=result.indicators_summary.period,
            indicators=[
                CostCenterIndicatorResponse(
                    cost_center_id=i.cost_center_id,
                    cost_center_code=i.cost_center_code,
                    period=i.period,
                    budgeted_amount=i.budgeted_amount,
                    actual_amount=i.actual_amount,
                    variance_amount=i.variance_amount,
                    execution_rate=i.execution_rate,
                    status=i.status,
                    currency=i.currency,
                )
                for i in result.indicators_summary.indicators
            ],
            total_budgeted=result.indicators_summary.total_budgeted,
            total_actual=result.indicators_summary.total_actual,
            total_variance=result.indicators_summary.total_variance,
            total_execution_rate=(result.indicators_summary.total_execution_rate),
            currency=result.indicators_summary.currency,
        ),
        is_fallback=result.is_fallback,
        ai_provider=result.ai_provider,
    )


@router.get(
    "/executive-summary/pdf",
    summary="Download formatted PDF executive briefing report",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Binary PDF executive briefing document.",
        }
    },
)
async def download_executive_summary_pdf(
    period: Annotated[
        str,
        Query(
            description="Target fiscal period in YYYY-MM format",
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        ),
    ],
    use_case: GenerateExecutiveSummaryUseCaseDep,
) -> Response:
    """Generate and stream a publication-ready PDF executive report.

    Args:
        period: Target fiscal period string (YYYY-MM).
        use_case: GenerateExecutiveSummaryUseCase dependency.

    Returns:
        Response: Streaming binary PDF with attachment content-disposition.
    """
    target_period = Period.from_string(period)
    result = await use_case.execute(target_period)
    pdf_bytes = ExecutiveSummaryPDFBuilder().build(result)

    filename = f"executive-summary-{period}.pdf"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=headers,
    )


@router.get(
    "/anomalies/{measurement_id}",
    response_model=list[AnomalyResponse],
    summary="Detect anomalies in a specific measurement",
)
async def analyze_measurement_anomalies(
    measurement_id: Annotated[UUID, Path(description="Measurement UUID")],
    use_case: AnalyzeAnomaliesUseCaseDep,
) -> list[AnomalyResponse]:
    """Inspect a measurement for abrupt allocation shifts and budget dumping.

    Args:
        measurement_id: Measurement UUID to analyze.
        use_case: AnalyzeAllocationAnomaliesUseCase dependency.

    Returns:
        list[AnomalyResponse]: Detected allocation anomalies.
    """
    anomalies = await use_case.analyze_measurement(measurement_id)
    return [
        AnomalyResponse(
            measurement_id=a.measurement_id,
            contract_id=a.contract_id,
            cost_center_id=a.cost_center_id,
            anomaly_type=a.anomaly_type.value,
            severity=a.severity.value,
            description=a.description,
            baseline_percentage=(
                str(a.baseline_percentage) if a.baseline_percentage else None
            ),
            actual_percentage=(
                str(a.actual_percentage) if a.actual_percentage else None
            ),
        )
        for a in anomalies
    ]

"""FastAPI router for Budget Indicators."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from src.indicators.application.dto import (
    ComputePeriodIndicatorsQuery,
    GenerateMaterialImpactQuery,
)
from src.indicators.domain.types import AggregationLevel, FocusMetric
from src.presentation.dependencies import (
    ComputePeriodIndicatorsUseCaseDep,
    MaterialImpactUseCaseDep,
)
from src.presentation.schemas.indicators import (
    CostCenterIndicatorResponse,
    PeriodIndicatorsResponse,
)
from src.presentation.schemas.materiality import (
    MaterialImpactReportResponse,
    MaterialityItemResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Budget Indicators"])


@router.get(
    "/indicators/{period}",
    response_model=PeriodIndicatorsResponse,
    summary="Compute period indicators for cost centers",
)
async def get_period_indicators(
    period: Annotated[str, Path(description="Fiscal period in YYYY-MM format")],
    use_case: ComputePeriodIndicatorsUseCaseDep,
    cost_center_id: Annotated[
        UUID | None,
        Query(description="Optional filter for specific cost center UUID"),
    ] = None,
) -> PeriodIndicatorsResponse:
    """Compute planned vs actual budget variance metrics.

    Args:
        period: Target fiscal period.
        use_case: ComputePeriodIndicatorsUseCase dependency.
        cost_center_id: Optional single cost center UUID filter.

    Returns:
        PeriodIndicatorsResponse: Consolidated variance metrics.
    """
    query = ComputePeriodIndicatorsQuery(
        period=period,
        cost_center_id=cost_center_id,
    )
    result = await use_case.execute(query)
    return PeriodIndicatorsResponse(
        period=result.period,
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
            for i in result.indicators
        ],
        total_budgeted=result.total_budgeted,
        total_actual=result.total_actual,
        total_variance=result.total_variance,
        total_execution_rate=result.total_execution_rate,
        currency=result.currency,
    )


@router.get(
    "/indicators/{period}/materiality-focus",
    response_model=MaterialImpactReportResponse,
    summary="Generate Pareto materiality and effort prioritization analysis",
)
async def get_materiality_focus(
    period: Annotated[str, Path(description="Fiscal period in YYYY-MM format")],
    use_case: MaterialImpactUseCaseDep,
    level: Annotated[
        AggregationLevel,
        Query(
            description=(
                "Aggregation level: cost_center, hierarchy, accounting_account"
            )
        ),
    ] = AggregationLevel.COST_CENTER,
    metric: Annotated[
        FocusMetric,
        Query(description="Focus metric for ranking: variance (overruns) or spend"),
    ] = FocusMetric.VARIANCE,
    cost_center_id: Annotated[
        UUID | None,
        Query(description="Optional cost center UUID filter"),
    ] = None,
    threshold_pct: Annotated[
        Decimal | None,
        Query(
            ge=Decimal("1.0"),
            le=Decimal("100.0"),
            description="Optional Pareto cutoff percentage",
        ),
    ] = None,
) -> MaterialImpactReportResponse:
    """Generate Pareto effort prioritization ranking across chosen segregation level.

    Args:
        period: Target fiscal period in YYYY-MM format.
        use_case: MaterialImpactUseCase dependency.
        level: Aggregation segregation dimension.
        metric: Focus metric for ranking.
        cost_center_id: Optional filter for a specific cost center.
        threshold_pct: Optional Pareto cutoff percentage.

    Returns:
        MaterialImpactReportResponse: Evaluated Pareto focus report.
    """
    query = GenerateMaterialImpactQuery(
        period=period,
        level=level.value,
        metric=metric.value,
        cost_center_id=cost_center_id,
        threshold_pct=threshold_pct,
    )
    result = await use_case.execute(query)
    return MaterialImpactReportResponse(
        period=result.period,
        aggregation_level=result.aggregation_level,
        focus_metric=result.focus_metric,
        cost_center_scope_id=result.cost_center_scope_id,
        total_baseline_budget=result.total_baseline_budget,
        total_baseline_spent=result.total_baseline_spent,
        total_baseline_overrun=result.total_baseline_overrun,
        items_count=len(result.items),
        items=[
            MaterialityItemResponse(
                entity_id=i.entity_id,
                code=i.code,
                name=i.name,
                level=i.level,
                planned_budget=i.planned_budget,
                actual_spent=i.actual_spent,
                variance=i.variance,
                metric_value=i.metric_value,
                share_of_total_pct=i.share_of_total_pct,
                cumulative_pct=i.cumulative_pct,
                priority=i.priority,
                rank=i.rank,
            )
            for i in result.items
        ],
        currency=result.currency,
    )

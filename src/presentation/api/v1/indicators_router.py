"""FastAPI router for Budget Indicators and What-If Simulations."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query

from src.indicators.application.dto import (
    AllocationShiftDTO,
    ComputePeriodIndicatorsQuery,
    SimulateScenarioCommand,
)
from src.presentation.dependencies import (
    ComputePeriodIndicatorsUseCaseDep,
    SimulateScenarioUseCaseDep,
)
from src.presentation.schemas.indicators import (
    CostCenterImpactResponse,
    CostCenterIndicatorResponse,
    PeriodIndicatorsResponse,
    ScenarioSimulateRequest,
    SimulationResultResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Budget Indicators & Simulations"])


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


@router.post(
    "/scenarios/simulate",
    response_model=SimulationResultResponse,
    summary="Execute in-memory what-if scenario simulation",
)
async def simulate_scenario(
    request: ScenarioSimulateRequest,
    use_case: SimulateScenarioUseCaseDep,
) -> SimulationResultResponse:
    """Evaluate contract inflation and allocation shifts in memory.

    Args:
        request: Simulation parameters payload.
        use_case: SimulateScenarioUseCase dependency.

    Returns:
        SimulationResultResponse: Comparative differential simulation report.
    """
    contract_adjustments: dict[UUID, Decimal] = {
        UUID(k): v for k, v in request.contract_inflation.items()
    }

    shifts = [
        AllocationShiftDTO(
            from_cost_center_id=s.from_cost_center_id,
            to_cost_center_id=s.to_cost_center_id,
            percentage_points=s.percentage_points,
            contract_id=s.contract_id,
        )
        for s in request.allocation_shifts
    ]

    command = SimulateScenarioCommand(
        scenario_name=request.name,
        period=request.period,
        contract_cost_adjustments=contract_adjustments,
        allocation_shifts=shifts,
    )
    result = await use_case.execute(command)

    total_baseline = sum(
        (imp.baseline_actual for imp in result.impacts), Decimal("0.00")
    )
    total_simulated = sum(
        (imp.simulated_actual for imp in result.impacts), Decimal("0.00")
    )
    total_delta = sum((imp.delta_actual for imp in result.impacts), Decimal("0.00"))
    overruns_count = sum(1 for imp in result.impacts if imp.new_overrun)

    return SimulationResultResponse(
        scenario_name=result.scenario_name,
        period=result.period,
        impacts=[
            CostCenterImpactResponse(
                cost_center_id=imp.cost_center_id,
                cost_center_code=imp.cost_center_code,
                baseline_actual=imp.baseline_actual,
                simulated_actual=imp.simulated_actual,
                delta_actual=imp.delta_actual,
                baseline_status=imp.baseline_status,
                simulated_status=imp.simulated_status,
                new_overrun=imp.new_overrun,
            )
            for imp in result.impacts
        ],
        new_overruns_count=overruns_count,
        total_baseline_actual=total_baseline,
        total_simulated_actual=total_simulated,
        total_delta=total_delta,
    )

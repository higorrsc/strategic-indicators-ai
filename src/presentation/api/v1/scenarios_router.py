"""FastAPI router for What-If scenario simulation endpoints."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter

from src.indicators.application.dto import (
    AllocationShiftDTO,
    SimulateScenarioCommand,
)
from src.presentation.dependencies import SimulateScenarioUseCaseDep
from src.presentation.schemas.indicators import (
    CostCenterImpactResponse,
    ScenarioSimulateRequest,
    SimulationResultResponse,
)

router = APIRouter(prefix="/api/v1", tags=["What-If Scenarios"])


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

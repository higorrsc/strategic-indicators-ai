"""FastAPI router for Budgeting bounded context endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, status

from src.budgeting.application.dto import (
    CreateCostCenterCommand,
    GetHierarchyBudgetQuery,
    SetBudgetTargetCommand,
)
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.presentation.dependencies import (
    CostCenterRepoDep,
    CreateCostCenterUseCaseDep,
    GetHierarchyBudgetUseCaseDep,
    SetBudgetTargetUseCaseDep,
)
from src.presentation.schemas.budgeting import (
    BudgetTargetResponse,
    BudgetTargetSetRequest,
    CostCenterCreateRequest,
    CostCenterResponse,
    HierarchyBudgetResponse,
)

router = APIRouter(prefix="/api/v1", tags=["Budgeting"])


@router.post(
    "/cost-centers",
    response_model=CostCenterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new cost center",
)
async def create_cost_center(
    request: CostCenterCreateRequest,
    use_case: CreateCostCenterUseCaseDep,
) -> CostCenterResponse:
    """Create and persist a new hierarchical cost center.

    Args:
        request: Cost center creation payload.
        use_case: CreateCostCenterUseCase dependency.

    Returns:
        CostCenterResponse: Created cost center.
    """
    command = CreateCostCenterCommand(
        code=request.code,
        name=request.name,
        parent_id=request.parent_id,
    )
    result = await use_case.execute(command)
    return CostCenterResponse(
        id=result.id,
        code=result.code,
        name=result.name,
        parent_id=result.parent_id,
        is_active=result.is_active,
    )


@router.get(
    "/cost-centers/{cost_center_id}",
    response_model=CostCenterResponse,
    summary="Get cost center by ID",
)
async def get_cost_center(
    cost_center_id: Annotated[UUID, Path(description="Cost center UUID")],
    repo: CostCenterRepoDep,
) -> CostCenterResponse:
    """Fetch cost center details by identifier.

    Args:
        cost_center_id: Cost center UUID.
        repo: Cost center repository dependency.

    Returns:
        CostCenterResponse: Cost center details.

    Raises:
        CostCenterNotFoundError: If cost center is not found.
    """
    cc = await repo.get_by_id(cost_center_id)
    if not cc:
        msg = f"Cost center '{cost_center_id}' not found."
        raise CostCenterNotFoundError(msg)

    return CostCenterResponse(
        id=cc.id,
        code=cc.code.value,
        name=cc.name,
        parent_id=cc.parent_id,
        is_active=cc.is_active,
    )


@router.get(
    "/cost-centers",
    response_model=list[CostCenterResponse],
    summary="List all active cost centers",
)
async def list_cost_centers(
    repo: CostCenterRepoDep,
) -> list[CostCenterResponse]:
    """List all registered active cost centers.

    Args:
        repo: Cost center repository dependency.

    Returns:
        list[CostCenterResponse]: List of cost centers.
    """
    centers = await repo.list_all(active_only=True)
    return [
        CostCenterResponse(
            id=cc.id,
            code=cc.code.value,
            name=cc.name,
            parent_id=cc.parent_id,
            is_active=cc.is_active,
        )
        for cc in centers
    ]


@router.post(
    "/budgets",
    response_model=BudgetTargetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set a periodic budget target",
)
async def set_budget_target(
    request: BudgetTargetSetRequest,
    use_case: SetBudgetTargetUseCaseDep,
) -> BudgetTargetResponse:
    """Register or update a planned budget amount.

    Args:
        request: Budget target request payload.
        use_case: SetBudgetTargetUseCase dependency.

    Returns:
        BudgetTargetResponse: Recorded budget target.
    """
    command = SetBudgetTargetCommand(
        cost_center_id=request.cost_center_id,
        period=request.period,
        category=request.category,
        amount=request.amount,
        currency=request.currency,
    )
    result = await use_case.execute(command)
    return BudgetTargetResponse(
        id=result.id,
        cost_center_id=result.cost_center_id,
        period=result.period,
        category=result.category,
        amount=result.amount,
        currency=result.currency,
    )


@router.get(
    "/cost-centers/{cost_center_id}/hierarchy-budget",
    response_model=HierarchyBudgetResponse,
    summary="Get aggregated hierarchical budget",
)
async def get_hierarchy_budget(
    cost_center_id: Annotated[UUID, Path(description="Cost center UUID")],
    period: Annotated[str, Query(description="Fiscal period YYYY-MM")],
    use_case: GetHierarchyBudgetUseCaseDep,
) -> HierarchyBudgetResponse:
    """Aggregate budget targets of a cost center and all its descendants.

    Args:
        cost_center_id: Target root/node cost center UUID.
        period: Target period string.
        use_case: GetHierarchyBudgetUseCase dependency.

    Returns:
        HierarchyBudgetResponse: Aggregated budget totals.
    """
    query = GetHierarchyBudgetQuery(
        cost_center_id=cost_center_id,
        period=period,
    )
    result = await use_case.execute(query)
    return HierarchyBudgetResponse(
        cost_center_id=result.cost_center_id,
        cost_center_code=result.cost_center_code,
        period=result.period,
        direct_total=result.direct_total,
        consolidated_total=result.consolidated_total,
        currency=result.currency,
    )

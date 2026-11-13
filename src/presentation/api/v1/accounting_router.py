"""FastAPI router for Accounting Accounts and Cost Center Breakdown endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request, status

from src.allocation.application.dto import (
    ListAccountingAccountsQuery,
    RegisterAccountingAccountCommand,
)
from src.presentation.dependencies import (
    GetCostCenterAccountingBreakdownUseCaseDep,
    ListAccountingAccountsUseCaseDep,
    RegisterAccountingAccountUseCaseDep,
)
from src.presentation.schemas.accounting import (
    AccountingAccountCreateRequest,
    AccountingAccountResponse,
    CostCenterAccountingBreakdownResponse,
    CostCenterAccountSpendResponse,
)
from src.presentation.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    build_pagination_links,
    calculate_total_pages,
)

router = APIRouter(prefix="/api/v1", tags=["Accounting Accounts"])


@router.post(
    "/accounting-accounts",
    response_model=AccountingAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new accounting account",
)
async def register_accounting_account(
    request: AccountingAccountCreateRequest,
    use_case: RegisterAccountingAccountUseCaseDep,
) -> AccountingAccountResponse:
    """Register a new accounting account with hierarchical code validation.

    Args:
        request: Account registration payload.
        use_case: RegisterAccountingAccountUseCase dependency.

    Returns:
        AccountingAccountResponse: Created accounting account representation.
    """
    command = RegisterAccountingAccountCommand(
        code=request.code,
        name=request.name,
        description=request.description,
    )
    result = await use_case.execute(command)
    return AccountingAccountResponse(
        id=result.id,
        code=result.code,
        name=result.name,
        description=result.description,
        is_active=result.is_active,
    )


@router.get(
    "/accounting-accounts",
    response_model=PaginatedResponse[AccountingAccountResponse],
    summary="List accounting accounts with pagination",
)
async def list_accounting_accounts(
    request: Request,
    use_case: ListAccountingAccountsUseCaseDep,
    active_only: Annotated[
        bool,
        Query(description="Filter by active status only"),
    ] = True,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    per_page: Annotated[
        int,
        Query(
            alias="perPage",
            ge=1,
            le=100,
            description="Number of items per page (1-100)",
        ),
    ] = 20,
) -> PaginatedResponse[AccountingAccountResponse]:
    """List registered accounting accounts with pagination and active filter.

    Args:
        request: FastAPI HTTP request object.
        use_case: ListAccountingAccountsUseCase dependency.
        active_only: Filter by active status.
        page: Page number (1-based).
        per_page: Number of items per page.

    Returns:
        PaginatedResponse[AccountingAccountResponse]: Paginated accounts envelope.
    """
    query = ListAccountingAccountsQuery(
        active_only=active_only,
        page=page,
        per_page=per_page,
    )
    result = await use_case.execute(query)

    data = [
        AccountingAccountResponse(
            id=a.id,
            code=a.code,
            name=a.name,
            description=a.description,
            is_active=a.is_active,
        )
        for a in result.items
    ]
    total_pages = calculate_total_pages(result.total_items, result.per_page)
    links = build_pagination_links(
        request=request,
        page=result.page,
        per_page=result.per_page,
        total_pages=total_pages,
    )
    return PaginatedResponse(
        data=data,
        pagination=PaginationMeta(
            page=result.page,
            per_page=result.per_page,
            total_items=result.total_items,
            total_pages=total_pages,
        ),
        links=links,
    )


@router.get(
    "/cost-centers/{cost_center_id}/accounting-breakdown",
    response_model=CostCenterAccountingBreakdownResponse,
    summary="Get cost center spend broken down by accounting account",
)
async def get_cost_center_accounting_breakdown(
    cost_center_id: Annotated[UUID, Path(description="Target Cost Center UUID")],
    period: Annotated[
        str,
        Query(
            description="Target fiscal period in YYYY-MM format",
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        ),
    ],
    use_case: GetCostCenterAccountingBreakdownUseCaseDep,
) -> CostCenterAccountingBreakdownResponse:
    """Retrieve spend breakdown by account for a cost center in a period.

    Args:
        cost_center_id: Cost Center UUID.
        period: Target fiscal period string (YYYY-MM).
        use_case: GetCostCenterAccountingBreakdownUseCase dependency.

    Returns:
        CostCenterAccountingBreakdownResponse: Aggregated account breakdown.
    """
    result = await use_case.execute(cost_center_id=cost_center_id, period_str=period)
    return CostCenterAccountingBreakdownResponse(
        cost_center_id=result.cost_center_id,
        period=result.period,
        total_spent=result.total_spent,
        accounts=[
            CostCenterAccountSpendResponse(
                accounting_account_id=acc.accounting_account_id,
                account_code=acc.account_code,
                account_name=acc.account_name,
                spent_amount=acc.spent_amount,
                share_pct=acc.share_pct,
            )
            for acc in result.accounts
        ],
    )

"""FastAPI router for vendor contract endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request, status

from src.allocation.application.dto import (
    AllocationShareDTO,
    ListContractsQuery,
    RegisterContractCommand,
)
from src.allocation.domain.exceptions import ContractNotFoundError
from src.presentation.dependencies import (
    ContractRepoDep,
    ListContractsUseCaseDep,
    RegisterContractUseCaseDep,
)
from src.presentation.schemas.allocation import (
    AllocationShareSchema,
    ContractCreateRequest,
    ContractResponse,
)
from src.presentation.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    build_pagination_links,
    calculate_total_pages,
)

router = APIRouter(prefix="/api/v1", tags=["Contracts"])


@router.post(
    "/contracts",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new supplier contract",
)
async def register_contract(
    request: ContractCreateRequest,
    use_case: RegisterContractUseCaseDep,
) -> ContractResponse:
    """Register vendor contract with optional default allocations.

    Args:
        request: Contract creation payload.
        use_case: RegisterContractUseCase dependency.

    Returns:
        ContractResponse: Registered contract.
    """
    command = RegisterContractCommand(
        code=request.code,
        supplier_id=request.supplier_id,
        title=request.title,
        default_allocations=[
            AllocationShareDTO(
                cost_center_id=a.cost_center_id,
                percentage=a.percentage,
                accounting_account_id=a.accounting_account_id,
            )
            for a in request.default_allocations
        ],
    )
    result = await use_case.execute(command)
    return ContractResponse(
        id=result.id,
        code=result.code,
        supplier_id=result.supplier_id,
        title=result.title,
        default_allocations=[
            AllocationShareSchema(
                cost_center_id=a.cost_center_id,
                percentage=a.percentage,
                accounting_account_id=a.accounting_account_id,
            )
            for a in result.default_allocations
        ],
        is_active=result.is_active,
    )


@router.get(
    "/contracts",
    response_model=PaginatedResponse[ContractResponse],
    summary="List vendor contracts",
)
async def list_contracts(
    request: Request,
    use_case: ListContractsUseCaseDep,
    active_only: Annotated[
        bool, Query(description="Filter active contracts only")
    ] = True,
    supplier_id: Annotated[
        UUID | None, Query(description="Optional supplier UUID filter")
    ] = None,
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
) -> PaginatedResponse[ContractResponse]:
    """Query vendor contracts with optional filtering and pagination.

    Args:
        request: FastAPI HTTP request object.
        use_case: ListContractsUseCase dependency.
        active_only: Whether to return only active contracts.
        supplier_id: Optional supplier UUID filter.
        page: Page number (1-based).
        per_page: Number of items per page.

    Returns:
        PaginatedResponse[ContractResponse]: Paginated contracts envelope.
    """
    result = await use_case.execute(
        ListContractsQuery(
            supplier_id=supplier_id,
            active_only=active_only,
            page=page,
            per_page=per_page,
        )
    )
    data = [
        ContractResponse(
            id=c.id,
            code=c.code,
            supplier_id=c.supplier_id,
            title=c.title,
            default_allocations=[
                AllocationShareSchema(
                    cost_center_id=a.cost_center_id,
                    percentage=a.percentage,
                    accounting_account_id=a.accounting_account_id,
                )
                for a in c.default_allocations
            ],
            is_active=c.is_active,
        )
        for c in result.items
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
    "/contracts/{contract_id}",
    response_model=ContractResponse,
    summary="Get contract details by ID",
)
async def get_contract(
    contract_id: Annotated[UUID, Path(description="Contract UUID")],
    repo: ContractRepoDep,
) -> ContractResponse:
    """Fetch contract details by identifier.

    Args:
        contract_id: Contract UUID.
        repo: Contract repository dependency.

    Returns:
        ContractResponse: Contract details.

    Raises:
        ContractNotFoundError: If contract is not found.
    """
    contract = await repo.get_by_id(contract_id)
    if not contract:
        msg = f"Contract '{contract_id}' not found."
        raise ContractNotFoundError(msg)

    return ContractResponse(
        id=contract.id,
        code=contract.code,
        supplier_id=contract.supplier_id,
        title=contract.title,
        default_allocations=[
            AllocationShareSchema(
                cost_center_id=a.cost_center_id,
                percentage=a.percentage.value,
                accounting_account_id=a.accounting_account_id,
            )
            for a in contract.default_allocations
        ],
        is_active=contract.is_active,
    )

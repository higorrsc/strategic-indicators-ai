"""FastAPI router for Cost Allocation bounded context endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Query, Request, status

from src.allocation.application.dto import (
    AllocationShareDTO,
    ApproveMeasurementCommand,
    ListContractsQuery,
    ListMeasurementsQuery,
    RegisterContractCommand,
    SubmitMeasurementCommand,
)
from src.allocation.domain.exceptions import (
    ContractNotFoundError,
    MeasurementNotFoundError,
)
from src.presentation.dependencies import (
    ApproveMeasurementUseCaseDep,
    ContractRepoDep,
    ListContractsUseCaseDep,
    ListMeasurementsUseCaseDep,
    MeasurementRepoDep,
    RegisterContractUseCaseDep,
    SubmitMeasurementUseCaseDep,
)
from src.presentation.schemas.allocation import (
    AllocationEntryResponse,
    AllocationShareSchema,
    ContractCreateRequest,
    ContractResponse,
    MeasurementResponse,
    MeasurementSubmitRequest,
)
from src.presentation.schemas.pagination import (
    PaginatedResponse,
    PaginationMeta,
    build_pagination_links,
    calculate_total_pages,
)

router = APIRouter(prefix="/api/v1", tags=["Cost Allocation"])


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


@router.post(
    "/measurements",
    response_model=MeasurementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a measurement expense",
)
async def submit_measurement(
    request: MeasurementSubmitRequest,
    use_case: SubmitMeasurementUseCaseDep,
) -> MeasurementResponse:
    """Submit financial measurement with exact penny reconciliation.

    Args:
        request: Measurement submission payload.
        use_case: SubmitMeasurementUseCase dependency.

    Returns:
        MeasurementResponse: Created measurement and calculated allocations.
    """
    custom_allocations = (
        [
            AllocationShareDTO(
                cost_center_id=a.cost_center_id,
                percentage=a.percentage,
                accounting_account_id=a.accounting_account_id,
            )
            for a in request.allocation_override
        ]
        if request.allocation_override is not None
        else None
    )

    command = SubmitMeasurementCommand(
        contract_id=request.contract_id,
        period=request.period,
        description=request.description,
        gross_amount=request.gross_amount,
        currency=request.currency,
        custom_allocations=custom_allocations,
    )
    result = await use_case.execute(command)
    return MeasurementResponse(
        id=result.id,
        contract_id=result.contract_id,
        period=result.period,
        description=result.description,
        gross_amount=result.gross_amount,
        currency=result.currency,
        state=result.state,
        entries=[
            AllocationEntryResponse(
                cost_center_id=e.cost_center_id,
                percentage=e.percentage,
                amount=e.amount,
                currency=e.currency,
                accounting_account_id=e.accounting_account_id,
            )
            for e in result.entries
        ],
    )


@router.post(
    "/measurements/{measurement_id}/approve",
    response_model=MeasurementResponse,
    summary="Approve a submitted measurement",
)
async def approve_measurement(
    measurement_id: Annotated[UUID, Path(description="Measurement UUID")],
    use_case: ApproveMeasurementUseCaseDep,
) -> MeasurementResponse:
    """Transition measurement to APPROVED, activating actual cost entries.

    Args:
        measurement_id: Measurement UUID.
        use_case: ApproveMeasurementUseCase dependency.

    Returns:
        MeasurementResponse: Approved measurement.
    """
    command = ApproveMeasurementCommand(measurement_id=measurement_id)
    result = await use_case.execute(command)
    return MeasurementResponse(
        id=result.id,
        contract_id=result.contract_id,
        period=result.period,
        description=result.description,
        gross_amount=result.gross_amount,
        currency=result.currency,
        state=result.state,
        entries=[
            AllocationEntryResponse(
                cost_center_id=e.cost_center_id,
                percentage=e.percentage,
                amount=e.amount,
                currency=e.currency,
                accounting_account_id=e.accounting_account_id,
            )
            for e in result.entries
        ],
    )


@router.get(
    "/measurements/{measurement_id}",
    response_model=MeasurementResponse,
    summary="Get measurement by ID",
)
async def get_measurement(
    measurement_id: Annotated[UUID, Path(description="Measurement UUID")],
    repo: MeasurementRepoDep,
) -> MeasurementResponse:
    """Fetch measurement details by identifier.

    Args:
        measurement_id: Measurement UUID.
        repo: Measurement repository dependency.

    Returns:
        MeasurementResponse: Measurement details.

    Raises:
        MeasurementNotFoundError: If measurement is not found.
    """
    measurement = await repo.get_by_id(measurement_id)
    if not measurement:
        msg = f"Measurement '{measurement_id}' not found."
        raise MeasurementNotFoundError(msg)

    return MeasurementResponse(
        id=measurement.id,
        contract_id=measurement.contract_id,
        period=str(measurement.period),
        description=measurement.description,
        gross_amount=measurement.gross_amount.amount,
        currency=measurement.gross_amount.currency,
        state=measurement.state.value,
        entries=[
            AllocationEntryResponse(
                cost_center_id=e.cost_center_id,
                percentage=e.percentage.value,
                amount=e.amount.amount,
                currency=e.amount.currency,
                accounting_account_id=e.accounting_account_id,
            )
            for e in measurement.entries
        ],
    )


@router.get(
    "/measurements",
    response_model=PaginatedResponse[MeasurementResponse],
    summary="List financial measurements",
)
async def list_measurements(
    request: Request,
    use_case: ListMeasurementsUseCaseDep,
    period: Annotated[
        str | None,
        Query(
            description="Optional fiscal period filter (YYYY-MM)",
            pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        ),
    ] = None,
    contract_id: Annotated[
        UUID | None, Query(description="Optional contract UUID filter")
    ] = None,
    state: Annotated[
        str | None,
        Query(
            description=(
                "Optional measurement state filter "
                "(DRAFT, SUBMITTED, APPROVED, CANCELLED)"
            )
        ),
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
) -> PaginatedResponse[MeasurementResponse]:
    """Query financial measurements with multi-criteria filtering and pagination.

    Args:
        request: FastAPI HTTP request object.
        use_case: ListMeasurementsUseCase dependency.
        period: Optional fiscal period filter.
        contract_id: Optional contract UUID filter.
        state: Optional measurement lifecycle state filter.
        page: Page number (1-based).
        per_page: Number of items per page.

    Returns:
        PaginatedResponse[MeasurementResponse]: Paginated measurements envelope.
    """
    result = await use_case.execute(
        ListMeasurementsQuery(
            period=period,
            contract_id=contract_id,
            state=state,
            page=page,
            per_page=per_page,
        )
    )
    data = [
        MeasurementResponse(
            id=m.id,
            contract_id=m.contract_id,
            period=m.period,
            description=m.description,
            gross_amount=m.gross_amount,
            currency=m.currency,
            state=m.state,
            entries=[
                AllocationEntryResponse(
                    cost_center_id=e.cost_center_id,
                    percentage=e.percentage,
                    amount=e.amount,
                    currency=e.currency,
                    accounting_account_id=e.accounting_account_id,
                )
                for e in m.entries
            ],
        )
        for m in result.items
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

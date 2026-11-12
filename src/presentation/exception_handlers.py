"""FastAPI exception handlers mapping domain exceptions to HTTP status codes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.allocation.domain.exceptions import (
    AllocationDomainError,
    AllocationReconciliationError,
    ContractNotFoundError,
    InvalidAllocationPercentageError,
    InvalidMeasurementStateError,
    MeasurementNotFoundError,
    SupplierNotFoundError,
)
from src.budgeting.domain.exceptions import (
    BudgetingDomainError,
    CircularCostCenterHierarchyError,
    CostCenterNotFoundError,
    DuplicateCostCenterCodeError,
    InvalidBudgetTargetError,
)
from src.indicators.domain.exceptions import (
    IndicatorsDomainError,
    SimulationParameterError,
)
from src.intelligence.domain.exceptions import (
    AIProviderError,
    IntelligenceDomainError,
)
from src.shared.domain.exceptions import (
    CurrencyMismatchError,
    DomainError,
    InvalidCostCenterCodeError,
    InvalidMonetaryAmountError,
    InvalidPercentageError,
    InvalidPeriodError,
)

if TYPE_CHECKING:
    from fastapi import FastAPI


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers for domain errors.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(CostCenterNotFoundError)
    @app.exception_handler(MeasurementNotFoundError)
    @app.exception_handler(ContractNotFoundError)
    @app.exception_handler(SupplierNotFoundError)
    async def not_found_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": exc.__class__.__name__},
        )

    @app.exception_handler(DuplicateCostCenterCodeError)
    @app.exception_handler(CircularCostCenterHierarchyError)
    @app.exception_handler(InvalidMeasurementStateError)
    async def conflict_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": exc.__class__.__name__},
        )

    @app.exception_handler(InvalidCostCenterCodeError)
    @app.exception_handler(InvalidBudgetTargetError)
    @app.exception_handler(InvalidAllocationPercentageError)
    @app.exception_handler(AllocationReconciliationError)
    @app.exception_handler(InvalidPeriodError)
    @app.exception_handler(InvalidPercentageError)
    @app.exception_handler(InvalidMonetaryAmountError)
    @app.exception_handler(CurrencyMismatchError)
    @app.exception_handler(SimulationParameterError)
    @app.exception_handler(AllocationDomainError)
    @app.exception_handler(BudgetingDomainError)
    @app.exception_handler(IndicatorsDomainError)
    @app.exception_handler(IntelligenceDomainError)
    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc), "error_type": exc.__class__.__name__},
        )

    @app.exception_handler(AIProviderError)
    async def ai_provider_error_handler(
        _request: Request, exc: AIProviderError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc), "error_type": exc.__class__.__name__},
        )

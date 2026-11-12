"""Domain exceptions for cost allocation bounded context."""

from src.shared.domain.exceptions import DomainError


class AllocationDomainError(DomainError):
    """Base exception for all allocation domain rule violations."""


class SupplierNotFoundError(AllocationDomainError):
    """Raised when a supplier is not found."""


class ContractNotFoundError(AllocationDomainError):
    """Raised when a contract is not found."""


class MeasurementNotFoundError(AllocationDomainError):
    """Raised when a measurement is not found."""


class InvalidAllocationPercentageError(AllocationDomainError):
    """Raised when allocation shares do not equal 100%."""


class InvalidMeasurementStateError(AllocationDomainError):
    """Raised when an invalid measurement lifecycle transition is attempted."""


class AllocationReconciliationError(AllocationDomainError):
    """Raised when monetary amounts cannot be reconciled exactly to gross total."""

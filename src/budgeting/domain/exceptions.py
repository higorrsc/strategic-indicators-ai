"""Domain exceptions for budgeting bounded context."""

from src.shared.domain.exceptions import DomainError


class BudgetingDomainError(DomainError):
    """Base exception for all budgeting domain rule violations."""


class CostCenterNotFoundError(BudgetingDomainError):
    """Raised when a requested cost center is not found."""


class DuplicateCostCenterCodeError(BudgetingDomainError):
    """Raised when a cost center with the same code already exists."""


class CircularCostCenterHierarchyError(BudgetingDomainError):
    """Raised when an operation would introduce a circular reference in hierarchy."""


class InvalidBudgetTargetError(BudgetingDomainError):
    """Raised when budget target parameters or values violate domain invariants."""

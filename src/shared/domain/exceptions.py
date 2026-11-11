"""Shared domain exceptions for clean architecture boundary."""


class DomainError(Exception):
    """Base exception for all domain rule violations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidMonetaryAmountError(DomainError):
    """Raised when a monetary amount is invalid."""


class CurrencyMismatchError(DomainError):
    """Raised when arithmetic is attempted on different currencies."""


class InvalidPercentageError(DomainError):
    """Raised when a percentage value violates constraints."""


class InvalidPeriodError(DomainError):
    """Raised when a fiscal period format or range is invalid."""


class InvalidCostCenterCodeError(DomainError):
    """Raised when a cost center code does not match required structure."""

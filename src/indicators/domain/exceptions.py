"""Domain exceptions for budget indicators and simulations."""

from src.shared.domain.exceptions import DomainError


class IndicatorsDomainError(DomainError):
    """Base exception for all indicators and simulation domain rule violations."""


class SimulationParameterError(IndicatorsDomainError):
    """Raised when simulation parameters are invalid."""

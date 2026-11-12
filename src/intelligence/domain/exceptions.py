"""Domain exceptions for strategic intelligence and AI."""

from src.shared.domain.exceptions import DomainError


class IntelligenceDomainError(DomainError):
    """Base exception for strategic intelligence errors."""


class AIProviderError(IntelligenceDomainError):
    """Raised when an AI provider fails during inference."""

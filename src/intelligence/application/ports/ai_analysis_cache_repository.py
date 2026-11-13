"""Repository port for AI analysis cache persistence."""

from __future__ import annotations

from typing import Protocol

from src.intelligence.domain.cache import AIAnalysisCache


class AIAnalysisCacheRepository(Protocol):
    """Interface defining persistence operations for AI analysis cache entries."""

    async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None:
        """Retrieve cached analysis by unique cache key."""
        ...

    async def save(self, cache: AIAnalysisCache) -> None:
        """Persist or update an AI analysis cache entry."""
        ...

    async def delete_by_key(self, cache_key: str) -> None:
        """Remove a cached analysis by key."""
        ...

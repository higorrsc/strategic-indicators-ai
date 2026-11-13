"""In-memory dictionary-backed implementation of AIAnalysisCacheRepository."""

from __future__ import annotations

from src.intelligence.application.ports.ai_analysis_cache_repository import (
    AIAnalysisCacheRepository,
)
from src.intelligence.domain.cache import AIAnalysisCache


class InMemoryAIAnalysisCacheRepository(AIAnalysisCacheRepository):
    """In-memory test double for AI analysis cache persistence."""

    def __init__(self) -> None:
        """Initialize in-memory cache dictionary storage."""
        self._storage: dict[str, AIAnalysisCache] = {}

    async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None:
        """Retrieve cached entry by key."""
        return self._storage.get(cache_key)

    async def save(self, cache: AIAnalysisCache) -> None:
        """Persist or update cache entry in dictionary."""
        self._storage[cache.cache_key] = cache

    async def delete_by_key(self, cache_key: str) -> None:
        """Remove cache entry from dictionary."""
        self._storage.pop(cache_key, None)

"""Session-managed intelligence repository wrappers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.intelligence.domain.cache import AIAnalysisCache
from src.intelligence.domain.repositories import AIAnalysisCacheRepository

from .sqlalchemy_ai_cache_repository import (
    SqlAlchemyAIAnalysisCacheRepository,
)


class SessionManagedAIAnalysisCacheRepository(AIAnalysisCacheRepository):
    """AIAnalysisCacheRepository wrapper executing operations in active sessions."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None:
        """Find cached analysis by key."""
        async with self._session_factory() as session:
            repo = SqlAlchemyAIAnalysisCacheRepository(session)
            return await repo.get_by_key(cache_key)

    async def save(self, cache: AIAnalysisCache) -> None:
        """Save or update cache entry and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyAIAnalysisCacheRepository(session)
            await repo.save(cache)
            await session.commit()

    async def delete_by_key(self, cache_key: str) -> None:
        """Delete cache entry by key and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyAIAnalysisCacheRepository(session)
            await repo.delete_by_key(cache_key)
            await session.commit()

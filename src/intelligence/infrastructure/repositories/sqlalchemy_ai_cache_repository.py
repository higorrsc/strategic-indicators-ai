"""SQLAlchemy implementation of AIAnalysisCacheRepository."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.intelligence.application.ports.ai_analysis_cache_repository import (
    AIAnalysisCacheRepository,
)
from src.intelligence.domain.cache import AIAnalysisCache
from src.intelligence.infrastructure.database.models import AIAnalysisCacheModel
from src.shared.domain.value_objects import Period, SupportedLanguage


class SqlAlchemyAIAnalysisCacheRepository(AIAnalysisCacheRepository):
    """SQLAlchemy persistence adapter for AI analysis cache."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with SQLAlchemy asynchronous session."""
        self._session = session

    async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None:
        """Retrieve cached analysis entity by unique cache key."""
        stmt = select(AIAnalysisCacheModel).where(
            AIAnalysisCacheModel.cache_key == cache_key
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def save(self, cache: AIAnalysisCache) -> None:
        """Persist or update an AI analysis cache entity (upsert semantics)."""
        stmt = select(AIAnalysisCacheModel).where(
            AIAnalysisCacheModel.cache_key == cache.cache_key
        )
        result = await self._session.execute(stmt)
        existing_model = result.scalar_one_or_none()

        if existing_model is not None:
            existing_model.data_hash = cache.data_hash
            existing_model.summary_payload = cache.summary_payload
            existing_model.created_at = cache.created_at
            existing_model.expires_at = cache.expires_at
            existing_model.updated_at = cache.updated_at
        else:
            model = AIAnalysisCacheModel(
                id=cache.id,
                cache_key=cache.cache_key,
                period=str(cache.period),
                language=cache.language.value,
                cost_center_id=cache.cost_center_id,
                accounting_account_id=cache.accounting_account_id,
                data_hash=cache.data_hash,
                summary_payload=cache.summary_payload,
                created_at=cache.created_at,
                expires_at=cache.expires_at,
                updated_at=cache.updated_at,
            )
            self._session.add(model)

        await self._session.flush()

    async def delete_by_key(self, cache_key: str) -> None:
        """Delete cached entry by cache key."""
        stmt = delete(AIAnalysisCacheModel).where(
            AIAnalysisCacheModel.cache_key == cache_key
        )
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: AIAnalysisCacheModel) -> AIAnalysisCache:
        """Map ORM model to domain entity."""
        return AIAnalysisCache(
            id=model.id,
            cache_key=model.cache_key,
            period=Period.from_string(model.period),
            language=SupportedLanguage(model.language),
            cost_center_id=model.cost_center_id,
            accounting_account_id=model.accounting_account_id,
            data_hash=model.data_hash,
            summary_payload=model.summary_payload,
            created_at=model.created_at,
            expires_at=model.expires_at,
            updated_at=model.updated_at,
        )

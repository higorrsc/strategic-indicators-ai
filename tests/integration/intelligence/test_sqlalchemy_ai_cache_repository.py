"""Integration tests for SqlAlchemyAIAnalysisCacheRepository."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.intelligence.domain.cache import AIAnalysisCache
from src.intelligence.infrastructure.repositories import (
    InMemoryAIAnalysisCacheRepository,
    SqlAlchemyAIAnalysisCacheRepository,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


@pytest.mark.asyncio
async def test_should_save_and_retrieve_cache_by_key(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyAIAnalysisCacheRepository(db_session)
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="abc123hash",
        summary_payload={"executive_summary": "Report text"},
        created_at=now,
        expires_at=now + timedelta(hours=24),
        updated_at=now,
    )
    await repo.save(cache)

    retrieved = await repo.get_by_key(cache.cache_key)
    assert retrieved is not None
    assert retrieved.cache_key == cache.cache_key
    assert retrieved.data_hash == "abc123hash"
    assert retrieved.summary_payload["executive_summary"] == "Report text"


@pytest.mark.asyncio
async def test_should_update_existing_cache_on_save(
    db_session: AsyncSession,
) -> None:
    repo = SqlAlchemyAIAnalysisCacheRepository(db_session)
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "Initial report"},
        created_at=now,
        expires_at=now + timedelta(hours=24),
        updated_at=now,
    )
    await repo.save(cache)

    # Renew/update
    cache.renew(
        "hash_v2",
        {"executive_summary": "Updated report"},
        ttl_hours=24,
        now=now,
    )
    await repo.save(cache)

    retrieved = await repo.get_by_key(cache.cache_key)
    assert retrieved is not None
    assert retrieved.data_hash == "hash_v2"
    assert retrieved.summary_payload["executive_summary"] == "Updated report"


@pytest.mark.asyncio
async def test_should_delete_cache_by_key(db_session: AsyncSession) -> None:
    repo = SqlAlchemyAIAnalysisCacheRepository(db_session)
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "To delete"},
        created_at=now,
        expires_at=now + timedelta(hours=24),
        updated_at=now,
    )
    await repo.save(cache)
    await repo.delete_by_key(cache.cache_key)

    assert await repo.get_by_key(cache.cache_key) is None


@pytest.mark.asyncio
async def test_in_memory_ai_cache_repository() -> None:
    repo = InMemoryAIAnalysisCacheRepository()
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_in_mem",
        summary_payload={"executive_summary": "Memory report"},
        created_at=now,
        expires_at=now + timedelta(hours=24),
        updated_at=now,
    )
    await repo.save(cache)
    retrieved = await repo.get_by_key(cache.cache_key)
    assert retrieved is not None
    assert retrieved.data_hash == "hash_in_mem"

    await repo.delete_by_key(cache.cache_key)
    assert await repo.get_by_key(cache.cache_key) is None

"""Unit tests for AIAnalysisCache domain entity and CacheStatus evaluation."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.intelligence.domain.cache import AIAnalysisCache, CacheStatus
from src.shared.domain.value_objects import Period, SupportedLanguage


def test_should_return_hit_when_hash_matches_and_unexpired() -> None:
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    status = cache.evaluate_status("hash_v1", force_refresh=False, now=now)
    assert status == CacheStatus.HIT


def test_should_return_invalidated_drift_when_hash_changes_even_if_unexpired() -> None:
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    status = cache.evaluate_status("hash_v2", force_refresh=False, now=now)
    assert status == CacheStatus.INVALIDATED_DRIFT


def test_should_return_expired_when_time_past_ttl_and_hash_unchanged() -> None:
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=25),
        expires_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=25),
    )
    status = cache.evaluate_status("hash_v1", force_refresh=False, now=now)
    assert status == CacheStatus.EXPIRED


def test_should_return_forced_refresh_when_force_flag_true() -> None:
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    status = cache.evaluate_status("hash_v1", force_refresh=True, now=now)
    assert status == CacheStatus.FORCED_REFRESH


def test_should_renew_cache_payload_and_expiry() -> None:
    now = datetime.now(UTC)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "old"},
        created_at=now - timedelta(hours=25),
        expires_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=25),
    )

    cache.renew("hash_v2", {"executive_summary": "new"}, ttl_hours=24, now=now)

    assert cache.data_hash == "hash_v2"
    assert cache.summary_payload == {"executive_summary": "new"}
    assert cache.created_at == now
    assert cache.expires_at == now + timedelta(hours=24)
    assert cache.updated_at == now
    assert (
        cache.evaluate_status("hash_v2", force_refresh=False, now=now)
        == CacheStatus.HIT
    )

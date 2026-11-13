"""Domain models and value objects for Strategic Intelligence caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

from src.shared.domain.value_objects import Period, SupportedLanguage


class CacheStatus(StrEnum):
    """Evaluation status of an AI analysis cache entry."""

    HIT = "HIT"
    MISS = "MISS"
    EXPIRED = "EXPIRED"
    INVALIDATED_DRIFT = "INVALIDATED_DRIFT"
    FORCED_REFRESH = "FORCED_REFRESH"


@dataclass
class AIAnalysisCache:
    """Domain entity representing a persisted or cached executive summary analysis."""

    id: UUID
    cache_key: str
    period: Period
    language: SupportedLanguage
    cost_center_id: UUID | None
    accounting_account_id: UUID | None
    data_hash: str
    summary_payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime
    updated_at: datetime

    def evaluate_status(
        self,
        current_data_hash: str,
        force_refresh: bool,
        now: datetime | None = None,
    ) -> CacheStatus:
        """Evaluate cache validity against current data hash and expiration.

        Precedence rules:
        1. force_refresh=True -> FORCED_REFRESH
        2. data_hash mismatch -> INVALIDATED_DRIFT (financial data changed)
        3. now >= expires_at -> EXPIRED (time expired)
        4. otherwise -> HIT (valid)
        """
        if force_refresh:
            return CacheStatus.FORCED_REFRESH

        if self.data_hash != current_data_hash:
            return CacheStatus.INVALIDATED_DRIFT

        current_time = now or datetime.now(UTC)
        expires_at = (
            self.expires_at
            if self.expires_at.tzinfo is not None
            else self.expires_at.replace(tzinfo=UTC)
        )
        if current_time >= expires_at:
            return CacheStatus.EXPIRED

        return CacheStatus.HIT

    def renew(
        self,
        current_data_hash: str,
        new_payload: dict[str, Any],
        ttl_hours: int,
        now: datetime | None = None,
    ) -> None:
        """Renew cache entry with fresh data hash, payload, and updated timestamps."""
        current_time = now or datetime.now(UTC)
        self.data_hash = current_data_hash
        self.summary_payload = new_payload
        self.created_at = current_time
        self.expires_at = current_time + timedelta(hours=ttl_hours)
        self.updated_at = current_time

"""Pydantic presentation schemas for Strategic Intelligence endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.presentation.schemas.indicators import PeriodIndicatorsResponse


class AnomalyResponse(BaseModel):
    """Response schema for an identified allocation anomaly."""

    model_config = ConfigDict(frozen=True)

    measurement_id: UUID
    contract_id: UUID
    cost_center_id: UUID
    anomaly_type: str
    severity: str
    description: str
    baseline_percentage: str | None = None
    actual_percentage: str | None = None


class ExecutiveSummaryResponseSchema(BaseModel):
    """Response schema for period executive summary report."""

    model_config = ConfigDict(frozen=True)

    period: str
    financial_health_status: str
    executive_summary: str
    root_causes: list[str]
    strategic_recommendations: list[str]
    anomalies: list[AnomalyResponse]
    indicators_summary: PeriodIndicatorsResponse
    is_fallback: bool
    ai_provider: str
    language: str = "pt-br"
    is_cached: bool = False
    cache_status: str = "MISS"
    cached_at: datetime | None = None

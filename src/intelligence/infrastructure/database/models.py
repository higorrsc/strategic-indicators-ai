"""SQLAlchemy ORM models for Strategic Intelligence caching."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class AIAnalysisCacheModel(Base):
    """SQLAlchemy model representing a cached executive summary analysis."""

    __tablename__ = "ai_analysis_cache"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    cache_key: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    period: Mapped[str] = mapped_column(String(7), index=True, nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    cost_center_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    accounting_account_id: Mapped[UUID | None] = mapped_column(
        Uuid, nullable=True, index=True
    )
    data_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    summary_payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

"""Integration test for data seeding and AI executive briefing."""

from __future__ import annotations

from decimal import Decimal

import pytest

from scripts.seed_ai_data import seed_data
from src.indicators.domain.models import IndicatorStatus
from src.intelligence.domain.models import AnomalyType
from src.presentation.dependencies import DependencyContainer
from src.shared.config.settings import Settings
from src.shared.infrastructure.database.base import Base


@pytest.mark.asyncio
async def test_should_seed_data_and_generate_ai_executive_summary() -> None:
    """Verify that seed_data populates financial records and triggers AI insights."""
    container = DependencyContainer()
    container.settings = Settings(AI_PROVIDER="fake")
    await container.init_database("sqlite+aiosqlite:///:memory:")

    assert container.engine is not None
    async with container.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        summary = await seed_data(
            container=container,
            clean=False,
            run_ai=True,
            target_period_str="2026-03",
        )

        assert summary is not None
        assert summary.financial_health_status == "CRITICAL"
        assert summary.is_fallback is False
        assert summary.ai_provider == "fake"

        # Verify indicators
        assert summary.indicators_summary.total_budgeted == Decimal("280000.00")
        assert summary.indicators_summary.total_actual == Decimal("245000.00")

        # Verify critical overrun cost centers (Cloud 1.1.1 and Marketing 1.3)
        overruns = [
            i
            for i in summary.indicators_summary.indicators
            if i.status == IndicatorStatus.CRITICAL_OVERRUN.value
        ]
        overrun_codes = {i.cost_center_code for i in overruns}
        assert "1.1.1" in overrun_codes
        assert "1.3" in overrun_codes

        # Verify detected anomaly
        assert len(summary.anomalies) >= 1
        shift_anomalies = [
            a
            for a in summary.anomalies
            if a.anomaly_type == AnomalyType.ABRUPT_ALLOCATION_SHIFT.value
        ]
        assert len(shift_anomalies) == 1
        assert "60.00% to 90.00%" in shift_anomalies[0].description

        # Verify root causes and recommendations generated
        assert len(summary.root_causes) >= 3
        assert len(summary.strategic_recommendations) >= 2

    finally:
        await container.close_database()

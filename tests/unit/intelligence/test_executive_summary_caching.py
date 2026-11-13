"""Unit tests for executive summary caching, data drift, and scoping."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio

from src.allocation.domain.entities.contract import Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)
from src.indicators.application.use_cases import ComputePeriodIndicatorsUseCase
from src.intelligence.application.use_cases import (
    AnalyzeAllocationAnomaliesUseCase,
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.domain.cache import CacheStatus
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIPort
from src.intelligence.infrastructure.repositories.in_memory_ai_cache_repository import (
    InMemoryAIAnalysisCacheRepository,
)
from src.shared.config.settings import Settings
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
    SupportedLanguage,
)


@pytest_asyncio.fixture
async def test_setup() -> dict[str, Any]:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    contract_repo = InMemoryContractRepository()
    meas_repo = InMemoryMeasurementRepository()
    cache_repo = InMemoryAIAnalysisCacheRepository()
    ai_port = FakeAIPort()

    cc1 = CostCenter(
        id=uuid4(),
        code=CostCenterCode("10.1"),
        name="IT Dept",
    )
    cc2 = CostCenter(
        id=uuid4(),
        code=CostCenterCode("10.2"),
        name="HR Dept",
    )
    await cc_repo.add(cc1)
    await cc_repo.add(cc2)

    p = Period.from_string("2026-11")
    await budget_repo.add(
        BudgetTarget(
            id=uuid4(),
            cost_center_id=cc1.id,
            period=p,
            amount=Money(Decimal("10000.00"), "USD"),
            category="OPEX",
        )
    )
    await budget_repo.add(
        BudgetTarget(
            id=uuid4(),
            cost_center_id=cc2.id,
            period=p,
            amount=Money(Decimal("5000.00"), "USD"),
            category="OPEX",
        )
    )

    contract = Contract(
        id=uuid4(),
        code="CTR-001",
        title="Cloud Services",
        supplier_id=uuid4(),
    )
    await contract_repo.add(contract)

    meas1 = Measurement(
        id=uuid4(),
        contract_id=contract.id,
        period=p,
        description="Services 1",
        gross_amount=Money(Decimal("8000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money(Decimal("8000.00"), "USD"),
                percentage=Percentage.from_number("100.00"),
            )
        ],
    )
    await meas_repo.add(meas1)

    indicators_uc = ComputePeriodIndicatorsUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=meas_repo,
    )
    anomalies_uc = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=meas_repo,
        indicators_use_case=indicators_uc,
    )
    settings = Settings(AI_CACHE_TTL_HOURS=24)

    use_case = GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_uc,
        anomalies_use_case=anomalies_uc,
        ai_port=ai_port,
        cache_repository=cache_repo,
        settings=settings,
    )

    return {
        "use_case": use_case,
        "cache_repo": cache_repo,
        "ai_port": ai_port,
        "meas_repo": meas_repo,
        "contract": contract,
        "cc1": cc1,
        "cc2": cc2,
        "period": p,
    }


@pytest.mark.asyncio
async def test_should_call_ai_on_first_request_and_hit_cache_on_second(
    test_setup: dict[str, Any],
) -> None:
    use_case = test_setup["use_case"]
    ai_port = test_setup["ai_port"]
    p = test_setup["period"]

    # 1. First request: MISS -> calls AI
    result1 = await use_case.execute(p, language=SupportedLanguage.PT_BR)
    assert result1.is_cached is False
    assert result1.cache_status == CacheStatus.MISS
    assert ai_port.call_count == 1

    # 2. Second request with same params: HIT -> uses cache, zero AI calls
    result2 = await use_case.execute(p, language=SupportedLanguage.PT_BR)
    assert result2.is_cached is True
    assert result2.cache_status == CacheStatus.HIT
    assert ai_port.call_count == 1
    assert result2.executive_summary == result1.executive_summary


@pytest.mark.asyncio
async def test_should_force_refresh_when_flag_is_true(
    test_setup: dict[str, Any],
) -> None:
    use_case = test_setup["use_case"]
    ai_port = test_setup["ai_port"]
    p = test_setup["period"]

    await use_case.execute(p)
    assert ai_port.call_count == 1

    # Force refresh
    result = await use_case.execute(p, force_refresh=True)
    assert result.is_cached is False
    assert result.cache_status == CacheStatus.FORCED_REFRESH
    assert ai_port.call_count == 2


@pytest.mark.asyncio
async def test_should_invalidate_cache_on_data_drift(
    test_setup: dict[str, Any],
) -> None:
    use_case = test_setup["use_case"]
    ai_port = test_setup["ai_port"]
    meas_repo = test_setup["meas_repo"]
    contract = test_setup["contract"]
    cc2 = test_setup["cc2"]
    p = test_setup["period"]

    # Initial call populates cache
    await use_case.execute(p)
    assert ai_port.call_count == 1

    # Add a new measurement in that period to cc2 (causing data drift)
    meas2 = Measurement(
        id=uuid4(),
        contract_id=contract.id,
        period=p,
        description="Services 2",
        gross_amount=Money(Decimal("3000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc2.id,
                amount=Money(Decimal("3000.00"), "USD"),
                percentage=Percentage.from_number("100.00"),
            )
        ],
    )
    await meas_repo.add(meas2)

    # Next call must detect data drift, invalidate cache and re-run AI
    result = await use_case.execute(p)
    assert result.is_cached is False
    assert result.cache_status == CacheStatus.INVALIDATED_DRIFT
    assert ai_port.call_count == 2


@pytest.mark.asyncio
async def test_should_expire_cache_when_time_past_ttl(
    test_setup: dict[str, Any],
) -> None:
    use_case = test_setup["use_case"]
    ai_port = test_setup["ai_port"]
    cache_repo = test_setup["cache_repo"]
    p = test_setup["period"]

    # Initial call
    await use_case.execute(p)
    assert ai_port.call_count == 1

    # Modify stored cache expires_at to be in the past
    cache_key = f"summary:p={p}:l=pt-br:cc=all:acc=all"
    entry = await cache_repo.get_by_key(cache_key)
    assert entry is not None
    entry.expires_at = datetime.now(UTC) - timedelta(hours=1)
    await cache_repo.save(entry)

    # Next call must detect expiration and re-run AI
    result = await use_case.execute(p)
    assert result.is_cached is False
    assert result.cache_status == CacheStatus.EXPIRED
    assert ai_port.call_count == 2


@pytest.mark.asyncio
async def test_should_scope_by_cost_center(
    test_setup: dict[str, Any],
) -> None:
    use_case = test_setup["use_case"]
    ai_port = test_setup["ai_port"]
    cc1 = test_setup["cc1"]
    cc2 = test_setup["cc2"]
    p = test_setup["period"]

    # Call scoped to cc1
    res_cc1 = await use_case.execute(p, cost_center_id=cc1.id)
    assert res_cc1.cache_status == CacheStatus.MISS
    assert len(res_cc1.indicators_summary.indicators) == 1
    assert res_cc1.indicators_summary.indicators[0].cost_center_id == cc1.id
    assert ai_port.call_count == 1

    # Second call scoped to cc1 hits cache
    res_cc1_cached = await use_case.execute(p, cost_center_id=cc1.id)
    assert res_cc1_cached.cache_status == CacheStatus.HIT
    assert ai_port.call_count == 1

    # Call scoped to cc2 misses cache (different scope)
    res_cc2 = await use_case.execute(p, cost_center_id=cc2.id)
    assert res_cc2.cache_status == CacheStatus.MISS
    assert res_cc2.indicators_summary.indicators[0].cost_center_id == cc2.id
    assert ai_port.call_count == 2

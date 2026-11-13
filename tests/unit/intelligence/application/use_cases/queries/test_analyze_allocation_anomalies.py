from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.exceptions import MeasurementNotFoundError
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
from src.indicators.application.use_cases.queries import (
    ComputePeriodIndicatorsUseCase,
)
from src.intelligence.application.use_cases.queries import (
    AnalyzeAllocationAnomaliesUseCase,
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIPort
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
    SupportedLanguage,
)


@pytest.mark.asyncio
async def test_should_analyze_measurement_and_raise_if_not_found() -> None:
    measurement_repo = InMemoryMeasurementRepository()
    use_case = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo
    )

    with pytest.raises(MeasurementNotFoundError):
        await use_case.analyze_measurement(uuid4())


@pytest.mark.asyncio
async def test_should_generate_executive_summary_happy_path() -> None:
    cost_center_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    contract_repo = InMemoryContractRepository()
    measurement_repo = InMemoryMeasurementRepository()

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="IT Infrastructure")
    await cost_center_repo.add(cc1)

    period_jan = Period(2026, 1)
    period_feb = Period(2026, 2)
    period_mar = Period(2026, 3)

    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc1.id,
            period=period_mar,
            category="Cloud",
            amount=Money.from_float_or_int(100000),
        )
    )

    contract = Contract(
        code="CT-CLOUD-2026",
        supplier_id=uuid4(),
        title="AWS Hosting",
        default_allocations=[
            AllocationShare(cost_center_id=cc1.id, percentage=Percentage.hundred())
        ],
    )
    await contract_repo.add(contract)

    # Past measurements: baseline 5%
    for p in [period_jan, period_feb]:
        past_m = Measurement(
            contract_id=contract.id,
            period=p,
            description="Historical Cloud",
            gross_amount=Money(Decimal("10000.00")),
            state=MeasurementState.APPROVED,
            entries=[
                AllocationEntry(
                    cost_center_id=cc1.id,
                    percentage=Percentage.from_number(Decimal("5.00")),
                    amount=Money(Decimal("500.00")),
                )
            ],
        )
        await measurement_repo.add(past_m)

    # Current measurement: sudden spike to 50%
    current_m = Measurement(
        contract_id=contract.id,
        period=period_mar,
        description="March Cloud Spike",
        gross_amount=Money(Decimal("100000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                percentage=Percentage.from_number(Decimal("50.00")),
                amount=Money(Decimal("50000.00")),
            )
        ],
    )
    await measurement_repo.add(current_m)

    indicators_use_case = ComputePeriodIndicatorsUseCase(
        cost_center_repository=cost_center_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )
    anomaly_use_case = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo,
        indicators_use_case=indicators_use_case,
    )
    fake_ai = FakeAIPort()
    summary_use_case = GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_use_case,
        anomalies_use_case=anomaly_use_case,
        ai_port=fake_ai,
    )

    summary = await summary_use_case.execute(
        period=period_mar,
        language=SupportedLanguage.PT_BR,
    )

    assert str(summary.period) == "2026-03"
    assert summary.financial_health_status in {
        "HEALTHY",
        "WARNING",
        "CRITICAL",
        "CONCERNING",
    }
    assert summary.is_fallback is False
    assert len(summary.executive_summary) > 0


@pytest.mark.asyncio
async def test_should_gracefully_fallback_when_ai_provider_fails() -> None:
    from tests.unit.intelligence.infrastructure.test_ai_adapters import FailingAIPort

    cost_center_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    measurement_repo = InMemoryMeasurementRepository()

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="IT Operations")
    await cost_center_repo.add(cc1)

    period = Period(2026, 3)
    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc1.id,
            period=period,
            category="Hardware",
            amount=Money.from_float_or_int(10000),
        )
    )

    indicators_use_case = ComputePeriodIndicatorsUseCase(
        cost_center_repository=cost_center_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )
    anomaly_use_case = AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo,
        indicators_use_case=indicators_use_case,
    )
    failing_ai = FailingAIPort()
    summary_use_case = GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_use_case,
        anomalies_use_case=anomaly_use_case,
        ai_port=failing_ai,
    )

    summary = await summary_use_case.execute(
        period=period,
        language=SupportedLanguage.EN_US,
    )

    assert summary.is_fallback is True
    assert "deterministic fallback" in summary.executive_summary.lower()
    assert summary.financial_health_status == "UNAVAILABLE (AI FALLBACK)"

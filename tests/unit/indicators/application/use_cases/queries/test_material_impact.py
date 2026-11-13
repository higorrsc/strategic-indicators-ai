"""Unit tests for GenerateMaterialImpactReportUseCase."""

from decimal import Decimal
from uuid import uuid4

import pytest

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.infrastructure.repositories.in_memory_allocation_repository import (
    InMemoryAccountingAccountRepository,
    InMemoryMeasurementRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.exceptions import CostCenterNotFoundError
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
)
from src.indicators.application.dto import GenerateMaterialImpactQuery
from src.indicators.application.use_cases.queries.material_impact import (
    GenerateMaterialImpactReportUseCase,
)
from src.shared.domain.value_objects import (
    AccountCode,
    CostCenterCode,
    Money,
    Percentage,
    Period,
)

_PCT_100 = Percentage.from_number("100.00")

_UseCaseSetup = tuple[
    GenerateMaterialImpactReportUseCase,
    InMemoryCostCenterRepository,
    InMemoryBudgetRepository,
    InMemoryMeasurementRepository,
    InMemoryAccountingAccountRepository,
]


@pytest.fixture
def use_case_setup() -> _UseCaseSetup:
    cc_repo = InMemoryCostCenterRepository()
    budget_repo = InMemoryBudgetRepository()
    meas_repo = InMemoryMeasurementRepository()
    acc_repo = InMemoryAccountingAccountRepository()
    use_case = GenerateMaterialImpactReportUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=meas_repo,
        accounting_account_repository=acc_repo,
    )
    return use_case, cc_repo, budget_repo, meas_repo, acc_repo


async def test_should_generate_materiality_at_cost_center_level_by_variance(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify cost_center level analysis ranks overrun cost centers by variance."""
    use_case, cc_repo, budget_repo, meas_repo, _ = use_case_setup
    period = Period.from_string("2026-03")

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="Cloud Ops")
    cc2 = CostCenter(code=CostCenterCode("1.2"), name="Core Dev")
    cc3 = CostCenter(code=CostCenterCode("1.3"), name="HR Support")
    await cc_repo.add(cc1)
    await cc_repo.add(cc2)
    await cc_repo.add(cc3)

    # CC1: budget 1000, spend 1800 -> overrun 800 (80%)
    # CC2: budget 1000, spend 1200 -> overrun 200 (20%)
    # CC3: budget 1000, spend 800  -> 0 overrun
    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc1.id,
            period=period,
            category="OPEX",
            amount=Money(Decimal("1000.00"), "USD"),
        )
    )
    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc2.id,
            period=period,
            category="OPEX",
            amount=Money(Decimal("1000.00"), "USD"),
        )
    )
    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc3.id,
            period=period,
            category="OPEX",
            amount=Money(Decimal("1000.00"), "USD"),
        )
    )

    m = Measurement(
        contract_id=uuid4(),
        period=period,
        description="Services",
        gross_amount=Money(Decimal("3800.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money(Decimal("1800.00"), "USD"),
                percentage=_PCT_100,
            ),
            AllocationEntry(
                cost_center_id=cc2.id,
                amount=Money(Decimal("1200.00"), "USD"),
                percentage=_PCT_100,
            ),
            AllocationEntry(
                cost_center_id=cc3.id,
                amount=Money(Decimal("800.00"), "USD"),
                percentage=_PCT_100,
            ),
        ],
    )
    await meas_repo.add(m)

    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="cost_center",
        metric="variance",
    )
    report = await use_case.execute(query)

    assert report.period == "2026-03"
    assert report.aggregation_level == "cost_center"
    assert report.focus_metric == "variance"
    assert report.total_baseline_overrun == Decimal("1000.00")
    assert report.total_baseline_spent == Decimal("3800.00")
    assert report.total_baseline_budget == Decimal("3000.00")
    assert len(report.items) == 3

    assert report.items[0].code == "1.1"
    assert report.items[0].share_of_total_pct == Decimal("80.00")
    assert report.items[0].priority == "IMMEDIATE_ACTION"

    assert report.items[1].code == "1.2"
    assert report.items[1].share_of_total_pct == Decimal("20.00")
    assert report.items[1].priority == "MONITOR"

    assert report.items[2].code == "1.3"
    assert report.items[2].share_of_total_pct == Decimal("0.00")
    assert report.items[2].priority == "LOW_IMPACT"


async def test_should_generate_materiality_at_hierarchy_level_by_spend(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify hierarchy level rolls up children to root parents and ranks by spend."""
    use_case, cc_repo, _, meas_repo, _ = use_case_setup
    period = Period.from_string("2026-03")

    root1 = CostCenter(code=CostCenterCode("1.0"), name="Technology Division")
    await cc_repo.add(root1)
    child1_1 = CostCenter(
        code=CostCenterCode("1.1"),
        name="Infra",
        parent_id=root1.id,
    )
    child1_2 = CostCenter(
        code=CostCenterCode("1.2"),
        name="Software",
        parent_id=root1.id,
    )
    await cc_repo.add(child1_1)
    await cc_repo.add(child1_2)

    root2 = CostCenter(code=CostCenterCode("2.0"), name="Operations Division")
    await cc_repo.add(root2)
    child2_1 = CostCenter(
        code=CostCenterCode("2.1"),
        name="Facilities",
        parent_id=root2.id,
    )
    await cc_repo.add(child2_1)

    # Technology: child 1.1 spent 7000, child 1.2 spent 2000 -> Total 9000 (90%)
    # Operations: child 2.1 spent 1000 -> Total 1000 (10%)
    m = Measurement(
        contract_id=uuid4(),
        period=period,
        description="Tech and ops invoices",
        gross_amount=Money(Decimal("10000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=child1_1.id,
                amount=Money(Decimal("7000.00"), "USD"),
                percentage=_PCT_100,
            ),
            AllocationEntry(
                cost_center_id=child1_2.id,
                amount=Money(Decimal("2000.00"), "USD"),
                percentage=_PCT_100,
            ),
            AllocationEntry(
                cost_center_id=child2_1.id,
                amount=Money(Decimal("1000.00"), "USD"),
                percentage=_PCT_100,
            ),
        ],
    )
    await meas_repo.add(m)

    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="hierarchy",
        metric="spend",
    )
    report = await use_case.execute(query)

    assert report.aggregation_level == "hierarchy"
    assert report.total_baseline_spent == Decimal("10000.00")
    assert len(report.items) == 2

    assert report.items[0].code == "1.0"
    assert report.items[0].name == "Technology Division"
    assert report.items[0].actual_spent == Decimal("9000.00")
    assert report.items[0].share_of_total_pct == Decimal("90.00")
    assert report.items[0].priority == "IMMEDIATE_ACTION"

    assert report.items[1].code == "2.0"
    assert report.items[1].name == "Operations Division"
    assert report.items[1].actual_spent == Decimal("1000.00")
    assert report.items[1].share_of_total_pct == Decimal("10.00")
    assert report.items[1].priority == "MONITOR"


async def test_should_generate_materiality_at_accounting_account_level_globally(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify accounting_account level aggregates across all cost centers."""
    use_case, cc_repo, _, meas_repo, acc_repo = use_case_setup
    period = Period.from_string("2026-03")

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="IT")
    cc2 = CostCenter(code=CostCenterCode("1.2"), name="MKT")
    await cc_repo.add(cc1)
    await cc_repo.add(cc2)

    acc_cloud = AccountingAccount(code=AccountCode("3.1.01"), name="Cloud Computing")
    acc_licenses = AccountingAccount(
        code=AccountCode("3.1.02"), name="Software Licenses"
    )
    await acc_repo.save(acc_cloud)
    await acc_repo.save(acc_licenses)

    m = Measurement(
        contract_id=uuid4(),
        period=period,
        description="IT allocations",
        gross_amount=Money(Decimal("10000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money(Decimal("6000.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc_cloud.id,
            ),
            AllocationEntry(
                cost_center_id=cc2.id,
                amount=Money(Decimal("2000.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc_cloud.id,
            ),
            AllocationEntry(
                cost_center_id=cc2.id,
                amount=Money(Decimal("2000.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc_licenses.id,
            ),
        ],
    )
    await meas_repo.add(m)

    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="accounting_account",
        metric="spend",
    )
    report = await use_case.execute(query)

    assert report.aggregation_level == "accounting_account"
    assert report.total_baseline_spent == Decimal("10000.00")
    assert len(report.items) == 2

    # Cloud: 6000 + 2000 = 8000 -> 80%
    assert report.items[0].code == "3.1.01"
    assert report.items[0].actual_spent == Decimal("8000.00")
    assert report.items[0].share_of_total_pct == Decimal("80.00")
    assert report.items[0].priority == "IMMEDIATE_ACTION"

    # Licenses: 2000 -> 20%
    assert report.items[1].code == "3.1.02"
    assert report.items[1].actual_spent == Decimal("2000.00")
    assert report.items[1].share_of_total_pct == Decimal("20.00")
    assert report.items[1].priority == "MONITOR"


async def test_should_generate_materiality_at_account_level_scoped_by_cost_center(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify account analysis scoped to single cost center and ranked by variance."""
    use_case, cc_repo, budget_repo, meas_repo, acc_repo = use_case_setup
    period = Period.from_string("2026-03")

    cc1 = CostCenter(code=CostCenterCode("1.1"), name="Cloud Engineering")
    await cc_repo.add(cc1)

    # Budget for CC1 = 10000
    await budget_repo.add(
        BudgetTarget(
            cost_center_id=cc1.id,
            period=period,
            category="OPEX",
            amount=Money(Decimal("10000.00"), "USD"),
        )
    )

    acc1 = AccountingAccount(code=AccountCode("3.1.01"), name="AWS Services")
    acc2 = AccountingAccount(code=AccountCode("3.1.02"), name="GCP Services")
    await acc_repo.save(acc1)
    await acc_repo.save(acc2)

    # Actual spend: 12000 (AWS: 9000, GCP: 3000) -> Overrun = 2000
    # AWS share of spend = 9000/12000 = 75% -> Overrun contribution = 1500 (75%)
    # GCP share of spend = 3000/12000 = 25% -> Overrun contribution = 500 (25%)
    m = Measurement(
        contract_id=uuid4(),
        period=period,
        description="Hosting invoices",
        gross_amount=Money(Decimal("12000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money(Decimal("9000.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc1.id,
            ),
            AllocationEntry(
                cost_center_id=cc1.id,
                amount=Money(Decimal("3000.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc2.id,
            ),
        ],
    )
    await meas_repo.add(m)

    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="accounting_account",
        metric="variance",
        cost_center_id=cc1.id,
    )
    report = await use_case.execute(query)

    assert report.cost_center_scope_id == cc1.id
    assert report.total_baseline_budget == Decimal("10000.00")
    assert report.total_baseline_spent == Decimal("12000.00")
    assert report.total_baseline_overrun == Decimal("2000.00")
    assert len(report.items) == 2

    assert report.items[0].code == "3.1.01"
    assert report.items[0].share_of_total_pct == Decimal("75.00")
    assert report.items[0].priority == "IMMEDIATE_ACTION"

    assert report.items[1].code == "3.1.02"
    assert report.items[1].share_of_total_pct == Decimal("25.00")
    assert report.items[1].priority == "IMMEDIATE_ACTION"


async def test_should_raise_cost_center_not_found_when_cost_center_filter_is_invalid(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify CostCenterNotFoundError if non-existent cost_center_id passed."""
    use_case, _, _, _, _ = use_case_setup
    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="accounting_account",
        cost_center_id=uuid4(),
    )
    with pytest.raises(CostCenterNotFoundError):
        await use_case.execute(query)


async def test_should_filter_by_threshold_pct(
    use_case_setup: _UseCaseSetup,
) -> None:
    """Verify threshold_pct filters report to Pareto vital subset."""
    use_case, cc_repo, _, meas_repo, acc_repo = use_case_setup
    period = Period.from_string("2026-03")

    cc = CostCenter(code=CostCenterCode("1.1"), name="General")
    await cc_repo.add(cc)

    acc1 = AccountingAccount(code=AccountCode("3.1.01"), name="Acc 1")
    acc2 = AccountingAccount(code=AccountCode("3.1.02"), name="Acc 2")
    acc3 = AccountingAccount(code=AccountCode("3.1.03"), name="Acc 3")
    await acc_repo.save(acc1)
    await acc_repo.save(acc2)
    await acc_repo.save(acc3)

    # 500, 300, 200 -> Acc1=50%, Acc2=30%, Acc3=20%
    m = Measurement(
        contract_id=uuid4(),
        period=period,
        description="General invoices",
        gross_amount=Money(Decimal("1000.00"), "USD"),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc.id,
                amount=Money(Decimal("500.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc1.id,
            ),
            AllocationEntry(
                cost_center_id=cc.id,
                amount=Money(Decimal("300.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc2.id,
            ),
            AllocationEntry(
                cost_center_id=cc.id,
                amount=Money(Decimal("200.00"), "USD"),
                percentage=_PCT_100,
                accounting_account_id=acc3.id,
            ),
        ],
    )
    await meas_repo.add(m)

    query = GenerateMaterialImpactQuery(
        period="2026-03",
        level="accounting_account",
        metric="spend",
        threshold_pct=Decimal("80.00"),
    )
    report = await use_case.execute(query)

    # Threshold 80% should return Acc 1 and Acc 2 (50% + 30% = 80%), excluding Acc 3
    assert len(report.items) == 2
    assert [i.code for i in report.items] == ["3.1.01", "3.1.02"]

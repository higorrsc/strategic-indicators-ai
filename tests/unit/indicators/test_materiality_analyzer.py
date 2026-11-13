"""Pure domain unit tests for MaterialityAnalyzer domain service."""

from decimal import Decimal
from uuid import uuid4

from src.indicators.domain.models import MaterialityCandidate
from src.indicators.domain.services.materiality_analyzer import (
    MaterialityAnalyzer,
)
from src.indicators.domain.types import (
    ActionPriority,
    AggregationLevel,
    FocusMetric,
)
from src.shared.domain.value_objects import Money


def test_should_rank_normal_spend_pareto_80_15_5_distribution() -> None:
    """Verify Pareto 80/15/5 distribution ranking and priority tiers for SPEND."""
    # 5 entities with spends: 600, 250, 100, 40, 10 -> Total = 1000
    # Shares:
    # Item 1: 600 -> 60.00% (cum: 60.00%, prev: 0.00% < 80) -> IMMEDIATE_ACTION
    # Item 2: 250 -> 25.00% (cum: 85.00%, prev: 60.00% < 80) -> IMMEDIATE_ACTION
    # Item 3: 100 -> 10.00% (cum: 95.00%, prev: 85.00% >= 80, < 95) -> MONITOR
    # Item 4: 40  -> 4.00%  (cum: 99.00%, prev: 95.00% >= 95) -> LOW_IMPACT
    # Item 5: 10  -> 1.00%  (cum: 100.00%, prev: 99.00% >= 95) -> LOW_IMPACT
    candidates = [
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.1",
            name="Cloud Infra",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("600.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.2",
            name="Consulting",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("250.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.3",
            name="Software Licenses",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("100.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.4",
            name="Office Supplies",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("40.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.5",
            name="Travel",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("10.00"), "USD"),
        ),
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.SPEND,
    )

    assert result.total_baseline_spent == Money(Decimal("1000.00"), "USD")
    assert len(result.items) == 5

    # Check ranks and priorities
    assert result.items[0].code == "1.1"
    assert result.items[0].rank == 1
    assert result.items[0].share_of_total_pct == Decimal("60.00")
    assert result.items[0].cumulative_pct == Decimal("60.00")
    assert result.items[0].priority == ActionPriority.IMMEDIATE_ACTION

    assert result.items[1].code == "1.2"
    assert result.items[1].rank == 2
    assert result.items[1].share_of_total_pct == Decimal("25.00")
    assert result.items[1].cumulative_pct == Decimal("85.00")
    assert result.items[1].priority == ActionPriority.IMMEDIATE_ACTION

    assert result.items[2].code == "1.3"
    assert result.items[2].rank == 3
    assert result.items[2].share_of_total_pct == Decimal("10.00")
    assert result.items[2].cumulative_pct == Decimal("95.00")
    assert result.items[2].priority == ActionPriority.MONITOR

    assert result.items[3].code == "1.4"
    assert result.items[3].rank == 4
    assert result.items[3].share_of_total_pct == Decimal("4.00")
    assert result.items[3].cumulative_pct == Decimal("99.00")
    assert result.items[3].priority == ActionPriority.LOW_IMPACT

    assert result.items[4].code == "1.5"
    assert result.items[4].rank == 5
    assert result.items[4].share_of_total_pct == Decimal("1.00")
    assert result.items[4].cumulative_pct == Decimal("100.00")
    assert result.items[4].priority == ActionPriority.LOW_IMPACT


def test_should_rank_overrun_variance_correctly() -> None:
    """Verify VARIANCE metric ranks positive budget overruns and ignores savings."""
    candidates = [
        # Overrun: spent 1500 vs budget 1000 -> +500 overrun
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.1",
            name="Overrun High",
            level=AggregationLevel.COST_CENTER,
            planned_budget=Money(Decimal("1000.00"), "USD"),
            actual_spent=Money(Decimal("1500.00"), "USD"),
        ),
        # Overrun: spent 600 vs budget 500 -> +100 overrun
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.2",
            name="Overrun Low",
            level=AggregationLevel.COST_CENTER,
            planned_budget=Money(Decimal("500.00"), "USD"),
            actual_spent=Money(Decimal("600.00"), "USD"),
        ),
        # Under budget: spent 700 vs budget 1000 -> -300 savings (0 overrun)
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.3",
            name="Savings Center",
            level=AggregationLevel.COST_CENTER,
            planned_budget=Money(Decimal("1000.00"), "USD"),
            actual_spent=Money(Decimal("700.00"), "USD"),
        ),
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.VARIANCE,
    )

    # Total overrun = 500 + 100 = 600
    assert result.total_baseline_overrun == Money(Decimal("600.00"), "USD")
    assert len(result.items) == 3

    # Item 1: 500 / 600 = 83.33%
    assert result.items[0].code == "1.1"
    assert result.items[0].rank == 1
    assert result.items[0].metric_value == Money(Decimal("500.00"), "USD")
    assert result.items[0].share_of_total_pct == Decimal("83.33")
    assert result.items[0].cumulative_pct == Decimal("83.33")
    assert result.items[0].priority == ActionPriority.IMMEDIATE_ACTION

    # Item 2: 100 / 600 = 16.67%
    assert result.items[1].code == "1.2"
    assert result.items[1].rank == 2
    assert result.items[1].metric_value == Money(Decimal("100.00"), "USD")
    assert result.items[1].share_of_total_pct == Decimal("16.67")
    assert result.items[1].cumulative_pct == Decimal("100.00")
    # Previous cumulative was 83.33% (>= 80% and < 95%) -> MONITOR
    assert result.items[1].priority == ActionPriority.MONITOR

    # Item 3: 0 overrun -> LOW_IMPACT
    assert result.items[2].code == "1.3"
    assert result.items[2].rank == 3
    assert result.items[2].metric_value == Money.zero("USD")
    assert result.items[2].share_of_total_pct == Decimal("0.00")
    assert result.items[2].priority == ActionPriority.LOW_IMPACT


def test_should_handle_zero_variance_period_gracefully() -> None:
    """Verify items get 0.00% share and LOW_IMPACT when on or under budget."""
    candidates = [
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.1",
            name="Balanced CC 1",
            level=AggregationLevel.COST_CENTER,
            planned_budget=Money(Decimal("1000.00"), "USD"),
            actual_spent=Money(Decimal("1000.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.2",
            name="Under Budget CC 2",
            level=AggregationLevel.COST_CENTER,
            planned_budget=Money(Decimal("2000.00"), "USD"),
            actual_spent=Money(Decimal("1500.00"), "USD"),
        ),
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.VARIANCE,
    )

    assert result.total_baseline_overrun == Money.zero("USD")
    assert len(result.items) == 2
    for item in result.items:
        assert item.metric_value == Money.zero("USD")
        assert item.share_of_total_pct == Decimal("0.00")
        assert item.cumulative_pct == Decimal("0.00")
        assert item.priority == ActionPriority.LOW_IMPACT


def test_should_handle_single_entity_scenario() -> None:
    """Verify single candidate takes 100% share and IMMEDIATE_ACTION if positive."""
    candidates = [
        MaterialityCandidate(
            entity_id=uuid4(),
            code="ROOT",
            name="Single Parent",
            level=AggregationLevel.HIERARCHY,
            actual_spent=Money(Decimal("45000.00"), "USD"),
        )
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.SPEND,
    )

    assert result.total_baseline_spent == Money(Decimal("45000.00"), "USD")
    assert len(result.items) == 1
    assert result.items[0].share_of_total_pct == Decimal("100.00")
    assert result.items[0].cumulative_pct == Decimal("100.00")
    assert result.items[0].priority == ActionPriority.IMMEDIATE_ACTION
    assert result.items[0].rank == 1


def test_should_handle_empty_candidates_list() -> None:
    """Verify empty candidates returns zero baseline without errors."""
    result = MaterialityAnalyzer.analyze(
        candidates=[],
        metric=FocusMetric.SPEND,
    )

    assert result.total_baseline_spent == Money.zero("USD")
    assert result.total_baseline_overrun == Money.zero("USD")
    assert result.total_baseline_budget is None
    assert result.items == []


def test_should_filter_items_by_threshold_cutoff() -> None:
    """Verify threshold_pct filters items to the Pareto cutoff group."""
    candidates = [
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.1",
            name="Major 1",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("500.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.2",
            name="Major 2",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("300.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=uuid4(),
            code="1.3",
            name="Minor 3",
            level=AggregationLevel.COST_CENTER,
            actual_spent=Money(Decimal("200.00"), "USD"),
        ),
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.SPEND,
        threshold_pct=Decimal("80.00"),
    )

    assert len(result.items) == 2
    assert [i.code for i in result.items] == ["1.1", "1.2"]


def test_should_handle_accounting_account_candidate_aggregation() -> None:
    """Verify candidates with ACCOUNTING_ACCOUNT level are evaluated consistently."""
    acc_id_1 = uuid4()
    acc_id_2 = uuid4()

    candidates = [
        MaterialityCandidate(
            entity_id=acc_id_1,
            code="3.1.01",
            name="Cloud Services",
            level=AggregationLevel.ACCOUNTING_ACCOUNT,
            actual_spent=Money(Decimal("7500.00"), "USD"),
            variance=Money(Decimal("1500.00"), "USD"),
        ),
        MaterialityCandidate(
            entity_id=acc_id_2,
            code="3.1.02",
            name="Software Subscriptions",
            level=AggregationLevel.ACCOUNTING_ACCOUNT,
            actual_spent=Money(Decimal("2500.00"), "USD"),
            variance=Money(Decimal("500.00"), "USD"),
        ),
    ]

    result = MaterialityAnalyzer.analyze(
        candidates=candidates,
        metric=FocusMetric.VARIANCE,
    )

    assert result.total_baseline_overrun == Money(Decimal("2000.00"), "USD")
    assert len(result.items) == 2
    assert result.items[0].code == "3.1.01"
    assert result.items[0].share_of_total_pct == Decimal("75.00")
    assert result.items[0].cumulative_pct == Decimal("75.00")
    assert result.items[0].priority == ActionPriority.IMMEDIATE_ACTION

    assert result.items[1].code == "3.1.02"
    assert result.items[1].share_of_total_pct == Decimal("25.00")
    assert result.items[1].cumulative_pct == Decimal("100.00")
    assert result.items[1].priority == ActionPriority.IMMEDIATE_ACTION

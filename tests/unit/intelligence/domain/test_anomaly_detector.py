from decimal import Decimal
from uuid import uuid4

from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.indicators.domain.models import (
    CostCenterIndicator,
    IndicatorStatus,
)
from src.intelligence.domain.models import (
    AnomalySeverity,
    AnomalyType,
)
from src.intelligence.domain.services.anomaly_detector import (
    AllocationAnomalyDetector,
)
from src.shared.domain.value_objects import (
    Money,
    Percentage,
    Period,
)


def test_should_detect_abrupt_allocation_percentage_shift() -> None:
    """Validate detection of sudden allocation shift against historical baseline."""
    contract_id = uuid4()
    cc_a = uuid4()
    cc_b = uuid4()
    period_jan = Period(2026, 1)
    period_feb = Period(2026, 2)
    period_mar = Period(2026, 3)

    past_1 = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_jan,
        description="January Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("5.00")),
                amount=Money(Decimal("500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("95.00")),
                amount=Money(Decimal("9500.00")),
            ),
        ],
    )
    past_2 = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_feb,
        description="February Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("5.00")),
                amount=Money(Decimal("500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("95.00")),
                amount=Money(Decimal("9500.00")),
            ),
        ],
    )

    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_mar,
        description="March Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("45.00")),
                amount=Money(Decimal("4500.00")),
            ),
            AllocationEntry(
                cost_center_id=cc_b,
                percentage=Percentage.from_number(Decimal("55.00")),
                amount=Money(Decimal("5500.00")),
            ),
        ],
    )

    anomalies = AllocationAnomalyDetector.detect_abrupt_shifts(
        current_measurement=current,
        historical_measurements=[past_1, past_2],
    )

    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.anomaly_type == AnomalyType.ABRUPT_ALLOCATION_SHIFT
    assert anomaly.severity == AnomalySeverity.HIGH
    assert anomaly.cost_center_id == cc_a
    assert anomaly.baseline_percentage == Percentage.from_number(Decimal("5.00"))
    assert anomaly.actual_percentage == Percentage.from_number(Decimal("45.00"))
    assert "Allocation share spiked" in anomaly.description


def test_should_not_detect_shift_when_variation_is_within_threshold() -> None:
    """Verify that shifts below threshold do not trigger false anomalies."""
    contract_id = uuid4()
    cc_a = uuid4()
    period_jan = Period(2026, 1)
    period_feb = Period(2026, 2)

    past = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_jan,
        description="January Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("50.00")),
                amount=Money(Decimal("5000.00")),
            ),
        ],
    )
    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period_feb,
        description="February Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=cc_a,
                percentage=Percentage.from_number(Decimal("60.00")),
                amount=Money(Decimal("6000.00")),
            ),
        ],
    )

    anomalies = AllocationAnomalyDetector.detect_abrupt_shifts(
        current_measurement=current,
        historical_measurements=[past],
    )

    assert anomalies == []


def test_should_detect_budget_dumping_to_relieve_overrun_center() -> None:
    """Detect dumping when allocation shifts to healthy center from critical center."""
    contract_id = uuid4()
    overrun_cc_id = uuid4()
    healthy_cc_id = uuid4()
    period = Period(2026, 3)

    past = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=Period(2026, 2),
        description="Past Month Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.APPROVED,
        entries=[
            AllocationEntry(
                cost_center_id=overrun_cc_id,
                percentage=Percentage.from_number(Decimal("80.00")),
                amount=Money(Decimal("8000.00")),
            ),
        ],
    )

    current = Measurement(
        id=uuid4(),
        contract_id=contract_id,
        period=period,
        description="Current Month Services",
        gross_amount=Money(Decimal("10000.00")),
        state=MeasurementState.SUBMITTED,
        entries=[
            AllocationEntry(
                cost_center_id=healthy_cc_id,
                percentage=Percentage.from_number(Decimal("80.00")),
                amount=Money(Decimal("8000.00")),
            ),
        ],
    )

    indicators = {
        overrun_cc_id: CostCenterIndicator(
            cost_center_id=overrun_cc_id,
            cost_center_code="CC-OVERRUN",
            period=period,
            budgeted_amount=Money(Decimal("1000.00")),
            actual_amount=Money(Decimal("5000.00")),
            variance_amount=Money(Decimal("-4000.00")),
            execution_rate=Percentage.from_number(Decimal("500.00")),
            status=IndicatorStatus.CRITICAL_OVERRUN,
        ),
        healthy_cc_id: CostCenterIndicator(
            cost_center_id=healthy_cc_id,
            cost_center_code="CC-HEALTHY",
            period=period,
            budgeted_amount=Money(Decimal("10000.00")),
            actual_amount=Money(Decimal("2000.00")),
            variance_amount=Money(Decimal("8000.00")),
            execution_rate=Percentage.from_number(Decimal("20.00")),
            status=IndicatorStatus.NORMAL,
        ),
    }

    anomalies = AllocationAnomalyDetector.detect_budget_dumping(
        measurement=current,
        indicators=indicators,
        contract_historical_measurements=[past],
    )

    assert len(anomalies) == 1
    anomaly = anomalies[0]
    assert anomaly.anomaly_type == AnomalyType.POTENTIAL_BUDGET_DUMPING
    assert anomaly.severity == AnomalySeverity.HIGH
    assert anomaly.cost_center_id == healthy_cc_id
    assert "healthy center" in anomaly.description

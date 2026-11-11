from decimal import Decimal

import pytest

from src.shared.domain.exceptions import (
    CurrencyMismatchError,
    InvalidCostCenterCodeError,
    InvalidMonetaryAmountError,
    InvalidPercentageError,
    InvalidPeriodError,
)
from src.shared.domain.value_objects import (
    CostCenterCode,
    Money,
    Percentage,
    Period,
)


class TestMoney:
    def test_should_create_money_and_quantize_cents(self) -> None:
        money = Money(Decimal("100.556"), "usd")
        assert money.amount == Decimal("100.56")
        assert money.currency == "USD"

    def test_should_create_from_float_or_int(self) -> None:
        m1 = Money.from_float_or_int(50, "BRL")
        m2 = Money.from_float_or_int(12.345, "BRL")
        assert m1.amount == Decimal("50.00")
        assert m2.amount == Decimal("12.35")

    def test_should_raise_on_invalid_amount(self) -> None:
        with pytest.raises(InvalidMonetaryAmountError):
            Money("not-a-number")  # type: ignore[arg-type]

    def test_should_add_and_subtract_same_currency(self) -> None:
        m1 = Money(Decimal("100.50"), "USD")
        m2 = Money(Decimal("49.50"), "USD")
        assert (m1 + m2) == Money(Decimal("150.00"), "USD")
        assert (m1 - m2) == Money(Decimal("51.00"), "USD")

    def test_should_raise_when_operating_different_currencies(self) -> None:
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("10.00"), "EUR")
        with pytest.raises(CurrencyMismatchError):
            _ = m1 + m2
        with pytest.raises(CurrencyMismatchError):
            _ = m1 - m2
        with pytest.raises(CurrencyMismatchError):
            _ = m1 < m2

    def test_should_multiply_and_divide(self) -> None:
        money = Money(Decimal("100.00"), "USD")
        assert money * 2 == Money(Decimal("200.00"), "USD")
        assert 3 * money == Money(Decimal("300.00"), "USD")
        assert money / 4 == Money(Decimal("25.00"), "USD")

    def test_should_divide_money_by_money_to_ratio(self) -> None:
        m1 = Money(Decimal("150.00"), "USD")
        m2 = Money(Decimal("300.00"), "USD")
        assert m1 / m2 == Decimal("0.5")

    def test_should_compare_correctly(self) -> None:
        m1 = Money(Decimal("10.00"), "USD")
        m2 = Money(Decimal("20.00"), "USD")
        assert m1 < m2
        assert m1 <= m2
        assert m2 > m1
        assert m2 >= m1
        assert m1 != m2

    def test_should_check_sign_status(self) -> None:
        assert Money(Decimal("1.00")).is_positive()
        assert Money(Decimal("-1.00")).is_negative()
        assert Money.zero().is_zero()


class TestPercentage:
    def test_should_create_from_number_and_ratio(self) -> None:
        p1 = Percentage.from_number("75.5")
        p2 = Percentage.from_ratio("0.755")
        assert p1.value == Decimal("75.50")
        assert p2.value == Decimal("75.50")
        assert p1.as_ratio() == Decimal("0.7550")

    def test_should_raise_on_invalid_percentage(self) -> None:
        with pytest.raises(InvalidPercentageError):
            Percentage.from_number("invalid")

    def test_should_add_and_compare(self) -> None:
        p1 = Percentage.from_number(40)
        p2 = Percentage.from_number(60)
        assert (p1 + p2) == Percentage.hundred()
        assert p1 < p2


class TestPeriod:
    def test_should_parse_valid_period_string(self) -> None:
        p = Period.from_string("2026-03")
        assert p.year == 2026
        assert p.month == 3
        assert str(p) == "2026-03"

    def test_should_reject_invalid_period_string(self) -> None:
        with pytest.raises(InvalidPeriodError):
            Period.from_string("2026-13")
        with pytest.raises(InvalidPeriodError):
            Period.from_string("invalid")

    def test_should_navigate_next_and_previous_periods(self) -> None:
        p_dec = Period(year=2026, month=12)
        assert p_dec.next_period() == Period(year=2027, month=1)

        p_jan = Period(year=2026, month=1)
        assert p_jan.previous_period() == Period(year=2025, month=12)

    def test_should_order_periods_chronologically(self) -> None:
        p1 = Period(year=2026, month=2)
        p2 = Period(year=2026, month=3)
        assert p1 < p2
        assert p2 > p1


class TestCostCenterCode:
    def test_should_parse_and_identify_hierarchy(self) -> None:
        root = CostCenterCode("1.0")
        child = CostCenterCode("1.0.1")
        assert root.level == 2
        assert child.level == 3
        assert child.parent_code == root
        assert root.parent_code == CostCenterCode("1")
        assert root.is_ancestor_of(child)
        assert child.is_descendant_of(root)

    def test_should_reject_invalid_syntax(self) -> None:
        with pytest.raises(InvalidCostCenterCodeError):
            CostCenterCode("")
        with pytest.raises(InvalidCostCenterCodeError):
            CostCenterCode("1..0")
        with pytest.raises(InvalidCostCenterCodeError):
            CostCenterCode(".1.0")

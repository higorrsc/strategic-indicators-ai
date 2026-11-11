"""Immutable Money value object representing monetary amounts and currencies."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from src.shared.domain.exceptions import (
    CurrencyMismatchError,
    InvalidMonetaryAmountError,
)

_CENT = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable Value Object representing monetary amounts with currency."""

    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        """Validate and quantize monetary amount to two decimal places."""
        if not isinstance(self.amount, Decimal):
            try:
                quantized = Decimal(str(self.amount)).quantize(
                    _CENT, rounding=ROUND_HALF_UP
                )
            except (InvalidOperation, ValueError, TypeError) as err:
                raise InvalidMonetaryAmountError(
                    f"Cannot convert amount '{self.amount}' to Decimal."
                ) from err
        else:
            quantized = self.amount.quantize(_CENT, rounding=ROUND_HALF_UP)

        object.__setattr__(self, "amount", quantized)
        object.__setattr__(self, "currency", self.currency.upper().strip())

    @classmethod
    def from_float_or_int(cls, value: float, currency: str = "USD") -> Money:
        """Create Money from numeric float or integer safely.

        Args:
            value: Numeric amount.
            currency: Three-letter ISO currency code.

        Returns:
            Money: Initialized instance.
        """
        return cls(amount=Decimal(str(value)), currency=currency)

    @classmethod
    def zero(cls, currency: str = "USD") -> Money:
        """Create Money instance with zero value.

        Args:
            currency: Three-letter ISO currency code.

        Returns:
            Money: Zero-valued instance.
        """
        return cls(amount=Decimal("0.00"), currency=currency)

    def _ensure_same_currency(self, other: Money) -> None:
        """Ensure other Money has identical currency.

        Args:
            other: Money object to compare.

        Raises:
            CurrencyMismatchError: If currencies do not match.
        """
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Currency mismatch: '{self.currency}' vs '{other.currency}'."
            )

    def __add__(self, other: object) -> Money:
        """Add two Money objects of identical currency."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: object) -> Money:
        """Subtract another Money object of identical currency."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: float | Decimal) -> Money:
        """Multiply Money by a scalar factor."""
        if isinstance(factor, (int, float, Decimal)):
            factor_dec = (
                Decimal(str(factor)) if not isinstance(factor, Decimal) else factor
            )
            return Money(amount=self.amount * factor_dec, currency=self.currency)
        return NotImplemented

    def __rmul__(self, factor: float | Decimal) -> Money:
        """Multiply Money by a scalar factor from the left."""
        return self.__mul__(factor)

    def __truediv__(self, divisor: float | Decimal | Money) -> Decimal | Money:
        """Divide Money by a scalar or another Money object."""
        if isinstance(divisor, Money):
            self._ensure_same_currency(divisor)
            if divisor.amount == Decimal("0.00"):
                raise ZeroDivisionError("Cannot divide Money by zero Money.")
            return self.amount / divisor.amount
        if isinstance(divisor, (int, float, Decimal)):
            divisor_dec = (
                Decimal(str(divisor)) if not isinstance(divisor, Decimal) else divisor
            )
            if divisor_dec == Decimal("0"):
                raise ZeroDivisionError("Cannot divide Money by zero scalar.")
            return Money(amount=self.amount / divisor_dec, currency=self.currency)
        return NotImplemented

    def __neg__(self) -> Money:
        """Return negated Money value."""
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> Money:
        """Return absolute Money value."""
        return Money(amount=abs(self.amount), currency=self.currency)

    def __lt__(self, other: object) -> bool:
        """Compare less than."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: object) -> bool:
        """Compare less than or equal."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: object) -> bool:
        """Compare greater than."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: object) -> bool:
        """Compare greater than or equal."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def is_positive(self) -> bool:
        """Check if amount is strictly positive.

        Returns:
            bool: True if amount > 0.
        """
        return self.amount > Decimal("0.00")

    def is_negative(self) -> bool:
        """Check if amount is strictly negative.

        Returns:
            bool: True if amount < 0.
        """
        return self.amount < Decimal("0.00")

    def is_zero(self) -> bool:
        """Check if amount is zero.

        Returns:
            bool: True if amount == 0.
        """
        return self.amount == Decimal("0.00")

    def __repr__(self) -> str:
        """Return developer representation."""
        return f"Money({self.amount}, '{self.currency}')"

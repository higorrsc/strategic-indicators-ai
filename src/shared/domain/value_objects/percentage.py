"""Percentage value object representing fractional or percentage points."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from src.shared.domain.exceptions import InvalidPercentageError

_ONE_HUNDRED = Decimal("100.00")


@dataclass(frozen=True, slots=True)
class Percentage:
    """Immutable Value Object representing percentage points (e.g. 70.0% = 70.0)."""

    value: Decimal

    def __post_init__(self) -> None:
        """Validate and quantize percentage value."""
        if not isinstance(self.value, Decimal):
            try:
                dec = Decimal(str(self.value))
            except (InvalidOperation, ValueError, TypeError) as err:
                raise InvalidPercentageError(
                    f"Cannot convert value '{self.value}' to Decimal percentage."
                ) from err
        else:
            dec = self.value

        object.__setattr__(
            self, "value", dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    @classmethod
    def from_ratio(cls, ratio: float | str | Decimal) -> Percentage:
        """Create Percentage from decimal ratio (e.g. 0.70 -> 70.0%).

        Args:
            ratio: Ratio between 0.0 and 1.0 (or greater).

        Returns:
            Percentage: Initialized percentage point object.
        """
        if isinstance(ratio, Decimal):
            return cls(value=ratio * _ONE_HUNDRED)
        try:
            return cls(value=Decimal(str(ratio)) * _ONE_HUNDRED)
        except (InvalidOperation, ValueError, TypeError) as err:
            raise InvalidPercentageError(
                f"Cannot convert ratio '{ratio}' to Decimal percentage."
            ) from err

    @classmethod
    def from_number(cls, num: float | str | Decimal) -> Percentage:
        """Create Percentage directly from percentage points (e.g. 70.0).

        Args:
            num: Number of percentage points.

        Returns:
            Percentage: Initialized percentage instance.
        """
        if isinstance(num, Decimal):
            return cls(value=num)
        try:
            return cls(value=Decimal(str(num)))
        except (InvalidOperation, ValueError, TypeError) as err:
            raise InvalidPercentageError(
                f"Cannot convert value '{num}' to Decimal percentage."
            ) from err

    @classmethod
    def hundred(cls) -> Percentage:
        """Return 100.00% instance."""
        return cls(value=_ONE_HUNDRED)

    @classmethod
    def zero(cls) -> Percentage:
        """Return 0.00% instance."""
        return cls(value=Decimal("0.00"))

    def as_ratio(self) -> Decimal:
        """Return percentage as a fractional ratio (e.g. 70% -> 0.70).

        Returns:
            Decimal: Fractional ratio.
        """
        return self.value / _ONE_HUNDRED

    def __add__(self, other: object) -> Percentage:
        """Add two percentage values."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return Percentage(value=self.value + other.value)

    def __sub__(self, other: object) -> Percentage:
        """Subtract another percentage value."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return Percentage(value=self.value - other.value)

    def __lt__(self, other: object) -> bool:
        """Compare less than."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        """Compare less than or equal."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        """Compare greater than."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        """Compare greater than or equal."""
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value >= other.value

    def __repr__(self) -> str:
        """Return developer representation."""
        return f"Percentage({self.value}%)"

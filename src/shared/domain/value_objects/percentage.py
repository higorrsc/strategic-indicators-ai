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
        """Create Percentage from decimal ratio (e.g. 0.70 -> 70.0%)."""
        if isinstance(ratio, Decimal):
            return cls(value=ratio * _ONE_HUNDRED)
        try:
            return cls(value=Decimal(str(ratio)) * _ONE_HUNDRED)
        except (InvalidOperation, ValueError, TypeError) as err:
            raise InvalidPercentageError(
                f"Cannot convert ratio '{ratio}' to Decimal percentage."
            ) from err

    @classmethod
    def from_number(cls, num: float | int | str | Decimal) -> Percentage:
        """Create Percentage directly from percentage points (e.g. 70.0)."""
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
        return cls(value=_ONE_HUNDRED)

    @classmethod
    def zero(cls) -> Percentage:
        return cls(value=Decimal("0.00"))

    def as_ratio(self) -> Decimal:
        """Return percentage as a fractional ratio (e.g. 70% -> 0.70)."""
        return self.value / _ONE_HUNDRED

    def __add__(self, other: object) -> Percentage:
        if not isinstance(other, Percentage):
            return NotImplemented
        return Percentage(value=self.value + other.value)

    def __sub__(self, other: object) -> Percentage:
        if not isinstance(other, Percentage):
            return NotImplemented
        return Percentage(value=self.value - other.value)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Percentage):
            return NotImplemented
        return self.value >= other.value

    def __repr__(self) -> str:
        return f"Percentage({self.value}%)"

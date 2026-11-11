from __future__ import annotations

import re
from dataclasses import dataclass

from src.shared.domain.exceptions import InvalidPeriodError

_PERIOD_REGEX = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True)
class Period:
    """Immutable Value Object representing a fiscal month period (YYYY-MM)."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if self.year < 1900 or self.year > 2100:
            raise InvalidPeriodError(
                f"Year {self.year} is out of realistic range (1900-2100)."
            )
        if self.month < 1 or self.month > 12:
            raise InvalidPeriodError(
                f"Month {self.month} is out of valid range (1-12)."
            )

    @classmethod
    def from_string(cls, period_str: str) -> Period:
        """Parse period string in YYYY-MM format."""
        match = _PERIOD_REGEX.match(period_str.strip())
        if not match:
            raise InvalidPeriodError(
                f"Period string '{period_str}' does not match format YYYY-MM."
            )
        year_str, month_str = match.groups()
        return cls(year=int(year_str), month=int(month_str))

    def next_period(self) -> Period:
        """Return the next sequential month period."""
        if self.month == 12:
            return Period(year=self.year + 1, month=1)
        return Period(year=self.year, month=self.month + 1)

    def previous_period(self) -> Period:
        """Return the preceding sequential month period."""
        if self.month == 1:
            return Period(year=self.year - 1, month=12)
        return Period(year=self.year, month=self.month - 1)

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"

    def __repr__(self) -> str:
        return f"Period('{self}')"

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (self.year, self.month) < (other.year, other.month)

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (self.year, self.month) <= (other.year, other.month)

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (self.year, self.month) > (other.year, other.month)

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Period):
            return NotImplemented
        return (self.year, self.month) >= (other.year, other.month)

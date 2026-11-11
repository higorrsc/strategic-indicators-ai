from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from src.budgeting.domain.exceptions import InvalidBudgetTargetError
from src.shared.domain.value_objects import Money, Period


@dataclass(slots=True)
class BudgetTarget:
    """Represents a planned budget target for a cost center, period, and category."""

    cost_center_id: UUID
    period: Period
    category: str
    amount: Money
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        trimmed_category = self.category.strip()
        if not trimmed_category:
            raise InvalidBudgetTargetError("Budget category cannot be empty.")
        self.category = trimmed_category
        if self.amount.is_negative():
            raise InvalidBudgetTargetError(
                f"Negative budget amount not allowed: {self.amount.amount}."
            )

    def update_amount(self, new_amount: Money) -> None:
        """Update the planned budget target amount."""
        if new_amount.is_negative():
            raise InvalidBudgetTargetError(
                f"Negative budget amount not allowed: {new_amount.amount}."
            )
        self.amount = new_amount

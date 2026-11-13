"""Exact penny cost allocation domain service."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from src.allocation.domain.entities.contract import AllocationShare
from src.allocation.domain.entities.measurement import AllocationEntry
from src.allocation.domain.exceptions import (
    AllocationDomainError,
    InvalidAllocationPercentageError,
)
from src.shared.domain.value_objects import Money, Percentage

_CENT = Decimal("0.01")


class ExactPennyAllocator:
    """Domain service that computes exact penny allocations and reconciles rounding."""

    @staticmethod
    def allocate(
        gross_amount: Money, shares: list[AllocationShare]
    ) -> list[AllocationEntry]:
        """Distribute gross amount across shares with exact penny reconciliation.

        Args:
            gross_amount: Total monetary expense.
            shares: List of cost center percentage shares.

        Returns:
            list[AllocationEntry]: Calculated allocation lines totaling gross_amount.
        """
        if not shares:
            raise AllocationDomainError(
                "Cannot allocate without at least one allocation share."
            )

        # 1. Validate percentage total equals 100.00%
        total_percentage = sum(
            (share.percentage.value for share in shares), Decimal("0.00")
        )
        if total_percentage != Decimal("100.00"):
            raise InvalidAllocationPercentageError(
                f"Allocation shares must sum to 100.00%, got {total_percentage}%."
            )

        # 2. Compute individual quantized amounts
        calculated: list[tuple[UUID, Percentage, Decimal, UUID | None]] = []
        for share in shares:
            ratio = share.percentage.as_ratio()
            raw_amount = gross_amount.amount * ratio
            quantized = raw_amount.quantize(_CENT, rounding=ROUND_HALF_UP)
            calculated.append(
                (
                    share.cost_center_id,
                    share.percentage,
                    quantized,
                    share.accounting_account_id,
                )
            )

        # 3. Calculate difference from rounding
        total_quantized = sum((item[2] for item in calculated), Decimal("0.00"))
        discrepancy = gross_amount.amount - total_quantized

        # 4. Reconcile discrepancy on the largest allocation line
        if discrepancy != Decimal("0.00"):
            max_idx = max(
                range(len(calculated)),
                key=lambda i: calculated[i][2],
            )
            cc_id, pct, amt, acc_id = calculated[max_idx]
            calculated[max_idx] = (cc_id, pct, amt + discrepancy, acc_id)

        # 5. Build final AllocationEntry list
        return [
            AllocationEntry(
                cost_center_id=cc_id,
                percentage=pct,
                amount=Money(amount=amt, currency=gross_amount.currency),
                accounting_account_id=acc_id,
            )
            for cc_id, pct, amt, acc_id in calculated
        ]

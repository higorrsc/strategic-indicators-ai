"""Domain service for Pareto effort prioritization and materiality analysis."""

from __future__ import annotations

from decimal import Decimal

from src.indicators.domain.models import (
    MaterialityAnalysisResult,
    MaterialityCandidate,
    MaterialityItem,
)
from src.indicators.domain.types import ActionPriority, FocusMetric
from src.shared.domain.value_objects import Money

_TIER_A_CUTOFF = Decimal("80.00")
_TIER_B_CUTOFF = Decimal("95.00")


class MaterialityAnalyzer:
    """Computes Pareto rankings, percentage contributions, and action priorities."""

    @classmethod
    def analyze(
        cls,
        candidates: list[MaterialityCandidate],
        metric: FocusMetric = FocusMetric.VARIANCE,
        threshold_pct: Decimal | None = None,
        currency: str = "USD",
    ) -> MaterialityAnalysisResult:
        """Analyze candidates to produce a Pareto effort prioritization report.

        Args:
            candidates: List of raw candidate entities with spend/budget metrics.
            metric: Focus metric to rank by (VARIANCE or SPEND).
            threshold_pct: Optional cutoff percentage (e.g. 80.00) to filter items.
            currency: Operating currency code.

        Returns:
            MaterialityAnalysisResult: Evaluated, ranked, and classified items.
        """
        if not candidates:
            return MaterialityAnalysisResult(
                metric=metric,
                total_baseline_budget=None,
                total_baseline_spent=Money.zero(currency),
                total_baseline_overrun=Money.zero(currency),
                items=[],
            )

        # Baseline sums
        total_spent = sum(
            (c.actual_spent for c in candidates),
            start=Money.zero(currency),
        )

        has_any_budget = any(c.planned_budget is not None for c in candidates)
        total_budget: Money | None = None
        if has_any_budget:
            total_budget = sum(
                (c.planned_budget for c in candidates if c.planned_budget is not None),
                start=Money.zero(currency),
            )

        # Compute overrun contribution for each candidate
        total_overrun = Money.zero(currency)
        for c in candidates:
            candidate_variance: Money | None = c.variance
            if candidate_variance is None and c.planned_budget is not None:
                candidate_variance = c.actual_spent - c.planned_budget

            if candidate_variance is not None and candidate_variance.amount > Decimal(
                "0.00"
            ):
                total_overrun += candidate_variance

        # Precompute candidate metrics and variances
        evaluated_entries: list[
            tuple[MaterialityCandidate, Money, Money | None, Money]
        ] = []
        for c in candidates:
            cand_variance: Money | None = c.variance
            if cand_variance is None and c.planned_budget is not None:
                cand_variance = c.actual_spent - c.planned_budget

            if metric == FocusMetric.SPEND:
                cand_metric_value = c.actual_spent
            else:  # FocusMetric.VARIANCE
                if cand_variance is not None and cand_variance.amount > Decimal("0.00"):
                    cand_metric_value = cand_variance
                else:
                    cand_metric_value = Money.zero(currency)

            evaluated_entries.append(
                (c, c.actual_spent, cand_variance, cand_metric_value)
            )

        # Sort descending by metric value, then spend, then code
        evaluated_entries.sort(
            key=lambda entry: (
                entry[3].amount,  # metric_value
                entry[1].amount,  # actual_spent
            ),
            reverse=True,
        )

        total_metric_amount = sum(
            (entry[3].amount for entry in evaluated_entries),
            start=Decimal("0.00"),
        )

        evaluated_items: list[MaterialityItem] = []
        cumulative_pct = Decimal("0.00")

        for idx, (cand, actual_spent, cand_variance, metric_value) in enumerate(
            evaluated_entries
        ):
            rank = idx + 1

            has_positive_metric = total_metric_amount > Decimal(
                "0.00"
            ) and metric_value.amount > Decimal("0.00")
            if has_positive_metric:
                share = (
                    metric_value.amount / total_metric_amount * Decimal("100.00")
                ).quantize(Decimal("0.01"))
                prev_cumulative = cumulative_pct
                cumulative_pct = min(
                    Decimal("100.00"),
                    (cumulative_pct + share).quantize(Decimal("0.01")),
                )

                if prev_cumulative < _TIER_A_CUTOFF:
                    priority = ActionPriority.IMMEDIATE_ACTION
                elif prev_cumulative < _TIER_B_CUTOFF:
                    priority = ActionPriority.MONITOR
                else:
                    priority = ActionPriority.LOW_IMPACT
            else:
                share = Decimal("0.00")
                priority = ActionPriority.LOW_IMPACT

            evaluated_items.append(
                MaterialityItem(
                    entity_id=cand.entity_id,
                    code=cand.code,
                    name=cand.name,
                    level=cand.level,
                    planned_budget=cand.planned_budget,
                    actual_spent=actual_spent,
                    variance=cand_variance,
                    metric_value=metric_value,
                    share_of_total_pct=share,
                    cumulative_pct=cumulative_pct,
                    priority=priority,
                    rank=rank,
                )
            )

        # Apply threshold filtering if requested
        if threshold_pct is not None and evaluated_items:
            cutoff = threshold_pct.quantize(Decimal("0.01"))
            filtered_items: list[MaterialityItem] = []
            for item in evaluated_items:
                # Include items where previous cumulative was below threshold
                prev_c = item.cumulative_pct - item.share_of_total_pct
                if item.rank == 1 or prev_c < cutoff:
                    filtered_items.append(item)
                else:
                    break
            evaluated_items = filtered_items

        return MaterialityAnalysisResult(
            metric=metric,
            total_baseline_budget=total_budget,
            total_baseline_spent=total_spent,
            total_baseline_overrun=total_overrun,
            items=evaluated_items,
        )

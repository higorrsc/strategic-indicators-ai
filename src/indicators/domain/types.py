"""Domain types and enums for strategic materiality and focus analysis."""

from enum import StrEnum


class AggregationLevel(StrEnum):
    """Aggregation segregation dimensions for materiality analysis."""

    COST_CENTER = "cost_center"
    HIERARCHY = "hierarchy"
    ACCOUNTING_ACCOUNT = "accounting_account"


class FocusMetric(StrEnum):
    """Metric used to calculate materiality ranking."""

    VARIANCE = "variance"
    SPEND = "spend"


class ActionPriority(StrEnum):
    """Pareto-based action priority classifications."""

    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"  # Pareto Class A: Top ~80%
    MONITOR = "MONITOR"  # Pareto Class B: Next ~15%
    LOW_IMPACT = "LOW_IMPACT"  # Pareto Class C: Remaining ~5%

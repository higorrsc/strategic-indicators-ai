"""Pydantic presentation schemas for Materiality & Effort Prioritization."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MaterialityItemResponse(BaseModel):
    """Response schema for a single ranked materiality focus item."""

    model_config = ConfigDict(frozen=True)

    entity_id: UUID | None = Field(
        default=None,
        description="Unique entity UUID, or None if unassigned.",
    )
    code: str = Field(description="Hierarchical code or identifier.")
    name: str = Field(description="Display name of the entity or account.")
    level: str = Field(
        description="Aggregation level: cost_center, hierarchy, or accounting_account.",
    )
    planned_budget: Decimal | None = Field(
        default=None, description="Planned budget amount."
    )
    actual_spent: Decimal = Field(description="Actual approved expenditure.")
    variance: Decimal | None = Field(
        default=None, description="Monetary variance (actual - planned)."
    )
    metric_value: Decimal = Field(
        description="Evaluated metric value for ranking."
    )
    share_of_total_pct: Decimal = Field(
        description="Percentage share of the total metric."
    )
    cumulative_pct: Decimal = Field(
        description="Cumulative percentage in the Pareto distribution."
    )
    priority: str = Field(
        description="Action priority: IMMEDIATE_ACTION, MONITOR, or LOW_IMPACT.",
    )
    rank: int = Field(description="1-based ordinal rank in Pareto distribution.")


class MaterialImpactReportResponse(BaseModel):
    """Response schema for consolidated Pareto effort prioritization report."""

    model_config = ConfigDict(frozen=True)

    period: str = Field(description="Target fiscal period in YYYY-MM format.")
    aggregation_level: str = Field(
        description="Aggregation segregation level.",
    )
    focus_metric: str = Field(
        description="Metric used for ranking (variance or spend).",
    )
    cost_center_scope_id: UUID | None = Field(
        default=None,
        description="Scoped Cost Center UUID if filtered.",
    )
    total_baseline_budget: Decimal | None = Field(
        default=None, description="Total baseline budget."
    )
    total_baseline_spent: Decimal = Field(
        description="Total baseline expenditure."
    )
    total_baseline_overrun: Decimal = Field(
        description="Total baseline budget overrun."
    )
    items_count: int = Field(
        description="Total number of ranked items returned."
    )
    items: list[MaterialityItemResponse] = Field(
        description="Ranked list of materiality items."
    )
    currency: str = Field(default="USD", description="Currency code.")

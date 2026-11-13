# Design: Material Impact & Effort Prioritization Analysis

## Architectural Flow

```text
Presentation Layer:
  GET /api/v1/indicators/{period}/materiality-focus?level=cost_center|hierarchy|accounting_account&cost_center_id=...&metric=variance|spend&threshold_pct=80
       ↓
Application Layer:
  GenerateMaterialImpactReportUseCase
       ↓
Domain Layer:
  Domain Service: MaterialityAnalyzer
  Entities & Value Objects:
    CostCenter, AccountingAccount, Money, Percentage, Period
  DTOs:
    MaterialityItemDTO, MaterialImpactReportDTO, ActionPriority, AggregationLevel, FocusMetric
```

## Domain Modeling

1. **Enums & Types:**

   ```python
   class AggregationLevel(str, Enum):
       COST_CENTER = "cost_center"  # Leaf individual cost centers
       HIERARCHY = "hierarchy"  # Consolidated root/parent nodes
       ACCOUNTING_ACCOUNT = "accounting_account"  # Breakdown by accounting accounts


   class FocusMetric(str, Enum):
       VARIANCE = "variance"  # Prioritizes budget overruns / deviations
       SPEND = "spend"  # Prioritizes absolute expenditure magnitude


   class ActionPriority(str, Enum):
       IMMEDIATE_ACTION = "IMMEDIATE_ACTION"  # Pareto Class A: Top 80% impact
       MONITOR = "MONITOR"  # Pareto Class B: Next 15% impact
       LOW_IMPACT = "LOW_IMPACT"  # Pareto Class C: Remaining 5%
   ```

2. **Domain Service: `MaterialityAnalyzer`**
   - Pure domain service with no HTTP/ORM dependencies.
   - Algorithm:
     1. Compute baseline totals: total target spend ($S_{total}$) and total target positive overrun ($V_{total}$).
     2. For each candidate element $i$:
        - Compute node spend $S_i$ and node variance $V_i$.
        - If `metric == SPEND`: weight $w_i = S_i / S_{total}$.
        - If `metric == VARIANCE`: weight $w_i = \max(0, V_i) / V_{total}$ (focusing on overrun contribution).
     3. Sort descending by $w_i$.
     4. Compute running cumulative percentage: $C_k = \sum_{j=1}^k w_j$.
     5. Classify `ActionPriority`:
        - If $C_{k-1} < 80.0\%$: `IMMEDIATE_ACTION` (Class A)
        - Else if $C_{k-1} < 95.0\%$: `MONITOR` (Class B)
        - Else: `LOW_IMPACT` (Class C)
     6. If `threshold_pct` is provided, tag items within threshold cutoff.

## Aggregation Mechanics by Level

- **`level == COST_CENTER`:** Evaluates all active leaf cost centers directly.
- **`level == HIERARCHY`:** Groups all leaf cost centers by their top-level root ancestor (e.g. `1.1` and `1.2` roll up to root `1.0`), producing a high-altitude executive division ranking.
- **`level == ACCOUNTING_ACCOUNT`:**
  - If `cost_center_id` is omitted: Groups all approved allocation entries across the entire organization by their `accounting_account_id`.
  - If `cost_center_id` is provided: Groups approved allocation entries belonging specifically to that Cost Center by their `accounting_account_id`.

## Application DTOs

```python
@dataclass(frozen=True)
class MaterialityItemDTO:
    entity_id: UUID
    code: str
    name: str
    level: str  # "cost_center", "hierarchy", or "accounting_account"
    planned_budget: Money | None
    actual_spent: Money
    variance: Money | None
    metric_value: Money
    share_of_total_pct: Decimal  # e.g., 42.5%
    cumulative_pct: Decimal  # e.g., 42.5%, then 71.2%, etc.
    priority: ActionPriority
    rank: int


@dataclass(frozen=True)
class MaterialImpactReportDTO:
    period: Period
    aggregation_level: AggregationLevel
    focus_metric: FocusMetric
    cost_center_scope_id: UUID | None
    total_baseline_budget: Money | None
    total_baseline_spent: Money
    total_baseline_overrun: Money
    items: list[MaterialityItemDTO]
```

## API Schemas & Presentation

- Route: `GET /api/v1/indicators/{period}/materiality-focus`
- Query Parameters:
  - `level: AggregationLevel = Query(default=AggregationLevel.COST_CENTER)`
  - `cost_center_id: UUID | None = Query(default=None)`
  - `metric: FocusMetric = Query(default=FocusMetric.VARIANCE)`
  - `threshold_pct: float | None = Query(default=None, ge=1.0, le=100.0)`
- Response Model: `MaterialImpactResponse` serialized with standard OpenAPI metadata.

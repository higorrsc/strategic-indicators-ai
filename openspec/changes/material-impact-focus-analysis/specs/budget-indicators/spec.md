# budget-indicators Specification Delta: Material Impact & Effort Prioritization

## Purpose

Calculates relative percentage materiality and cumulative Pareto distribution of expenditures and budget variances across Cost Centers, Hierarchical Branches, and Accounting Accounts to guide analyst focus toward high-impact areas.

## Requirements

### Requirement: Relative Materiality and Effort Prioritization Analysis

The system SHALL compute relative percentage contribution metrics for budget expenditures and variances, ranking entities by their cumulative impact across selectable segregation dimensions (`cost_center`, `hierarchy`, and `accounting_account`).

#### Scenario: Compute effort prioritization at Cost Center level by overrun

- **WHEN** an analyst requests materiality focus for period "2026-03" with `level=cost_center` and `metric=variance`
- **THEN** the system returns a descending-ranked list of cost centers contributing to total budget variance, calculating each center's percentage share of total overrun, cumulative overrun percentage, and Pareto action priority (`IMMEDIATE_ACTION`, `MONITOR`, or `LOW_IMPACT`)

#### Scenario: Compute effort prioritization at Hierarchy level by total spend

- **WHEN** an analyst requests materiality focus for period "2026-03" with `level=hierarchy` and `metric=spend`
- **THEN** the system aggregates all expenditures up to root-level parent cost centers, calculating each parent branch's percentage share of the company's total spend and cumulative spend percentage

#### Scenario: Compute effort prioritization at Accounting Account level globally

- **WHEN** an analyst requests materiality focus for period "2026-03" with `level=accounting_account` and `metric=spend`
- **THEN** the system aggregates expenditures across all cost centers grouped by Accounting Account, returning each account's total spent amount, percentage share of corporate spend, and cumulative Pareto ranking

#### Scenario: Compute effort prioritization at Accounting Account level within a specific Cost Center

- **WHEN** an analyst requests materiality focus for period "2026-03" with `level=accounting_account`, `cost_center_id="<uuid>"`, and `metric=variance`
- **THEN** the system scopes the analysis to allocations of that specific cost center, ranking the contributing accounting accounts by their share of the cost center's variance

#### Scenario: Filter by Pareto threshold cutoff

- **WHEN** a client requests materiality focus with `threshold_pct=80`
- **THEN** the system filters or highlights the vital subset of entities that collectively account for up to 80% of the target metric (Pareto Class A)

#### Scenario: Handle zero-variance period gracefully

- **WHEN** all entities operate exactly on budget with zero net variance
- **THEN** the system returns a neutral report indicating zero variance contribution without division-by-zero errors

# budget-indicators Specification

## Purpose
Calculates deterministic budget execution indicators, variance metrics, and performs forward-looking what-if scenario simulations.

## Requirements

### Requirement: Deterministic Budget vs Actual Calculation

The system SHALL compute actual expenditures per cost center and period by aggregating all approved allocation entries and comparing against budgeted targets.

#### Scenario: Normal budget consumption calculation

- **WHEN** cost center "1.1" has budget $50,000.00 and approved allocations totaling $35,000.00 in period "2026-03"
- **THEN** the system calculates variance -$15,000.00, execution rate 70.0%, and status "NORMAL"

#### Scenario: Budget overrun detection

- **WHEN** cost center "1.1" has budget $50,000.00 and approved allocations totaling $55,000.00 in period "2026-03"
- **THEN** the system calculates variance +$5,000.00, execution rate 110.0%, and status "CRITICAL_OVERRUN"

#### Scenario: Hierarchical consolidated variance

- **WHEN** querying indicators for parent cost center "1.0" containing child nodes "1.1" and "1.2"
- **THEN** the system aggregates all budgeted targets and approved allocations from both child nodes into the consolidated indicator

### Requirement: What-If Scenario Simulation

The system SHALL simulate hypothetical budget scenarios by applying cost adjustments and allocation shift parameters in memory without persisting mutations.

#### Scenario: Simulate supplier inflation adjustment

- **WHEN** a simulation request specifies a +15% cost increase on contract "CT-2026-001" for period "2026-03"
- **THEN** the system returns simulated variance and identifies which cost centers enter overrun status under the adjusted conditions

#### Scenario: Simulate allocation weight reallocation

- **WHEN** a simulation shifts 20% of allocation from cost center "1.1" to "1.2"
- **THEN** the system returns a comparative differential table contrasting baseline indicators against simulated indicators

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

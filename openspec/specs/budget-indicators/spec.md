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

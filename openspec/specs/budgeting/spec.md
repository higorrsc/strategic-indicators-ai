# budgeting Specification

## Purpose
Enables management of hierarchical organizational cost centers and definition of periodic expense budget plans.

## Requirements

### Requirement: Cost Center Hierarchy Management

The system SHALL support creating and maintaining cost centers organized in an arbitrary-depth tree hierarchy with code validation.

#### Scenario: Create a root cost center

- **WHEN** an administrator creates a cost center with code "1.0", name "Executive Board", and no parent
- **THEN** the system persists the root cost center with active status and zero child nodes

#### Scenario: Create a child cost center

- **WHEN** an administrator creates a cost center with code "1.1", name "Information Technology", and parent "1.0"
- **THEN** the system links the child cost center to parent "1.0" and reflects the relationship in hierarchy queries

#### Scenario: Prevent circular cost center reference

- **WHEN** an update attempts to assign a cost center's child node as its own parent
- **THEN** the system rejects the operation with a business rule validation error

### Requirement: Periodic Budget Allocation

The system SHALL allow setting budget targets per cost center, fiscal period (YYYY-MM), and expense category.

#### Scenario: Set periodic budget target

- **WHEN** a finance manager creates a budget of $50,000.00 for cost center "1.1", period "2026-03", and category "Cloud Infrastructure"
- **THEN** the system registers the planned budget record and makes it available for variance calculations

#### Scenario: Reject negative budget target

- **WHEN** a request submits a planned budget amount less than zero
- **THEN** the system rejects the request with an invalid monetary value error

#### Scenario: Aggregate hierarchical budget

- **WHEN** querying the consolidated budget for parent cost center "1.0" in period "2026-03"
- **THEN** the system returns the sum of direct budgets of "1.0" plus all its descendants

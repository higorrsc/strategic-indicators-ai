# cost-allocation Specification

## Purpose
Manages contracts, suppliers, financial measurements, and flexible cost allocation distribution across cost centers with strict monetary integrity.

## Requirements

### Requirement: Contract and Supplier Management

The system SHALL register suppliers and contracts associated with default suggested cost allocation templates.

#### Scenario: Register new contract with default allocation

- **WHEN** a user registers contract "CT-2026-001" with supplier "Acme Cloud" and a default split of 70% to "1.1" and 30% to "1.2"
- **THEN** the system stores the active contract and associates the default allocation template

### Requirement: Measurement Registration and Lifecycle

The system SHALL track financial measurements through explicit lifecycle states: DRAFT, SUBMITTED, APPROVED, and CANCELLED.

#### Scenario: Submit draft measurement for approval

- **WHEN** a user submits a valid measurement in DRAFT state with gross amount $10,000.00 for period "2026-03"
- **THEN** the measurement transitions to SUBMITTED state awaiting financial approval

#### Scenario: Approve measurement activates allocation entries

- **WHEN** an authorized approver approves a SUBMITTED measurement
- **THEN** the measurement transitions to APPROVED and its allocation entries become effective in actual budget calculations

#### Scenario: Reject allocation modification on approved measurement

- **WHEN** a user attempts to edit allocation lines of an APPROVED measurement
- **THEN** the system rejects the modification with an invalid state transition error

### Requirement: Flexible Cost Allocation Rules

The system SHALL validate that cost allocation entries distributed across cost centers sum up exactly to 100% of the gross measurement amount.

#### Scenario: Override default contract allocation on measurement

- **WHEN** creating a measurement for contract "CT-2026-001" with custom distribution 60% to "1.1" and 40% to "1.2" instead of the default template
- **THEN** the system accepts the custom allocation and records the specific measurement distribution

#### Scenario: Reject allocation exceeding 100 percent

- **WHEN** a measurement allocation defines entries summing to 105% of the gross value
- **THEN** the system rejects the allocation with an apportionment sum violation error

#### Scenario: Exact penny rounding reconciliation

- **WHEN** distributing $1,000.00 equally across 3 cost centers (33.333...%)
- **THEN** the domain allocation service reconciles rounding so the sum of monetary entries equals exactly $1,000.00 ($333.34, $333.33, $333.33)

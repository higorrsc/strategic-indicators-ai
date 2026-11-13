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

### Requirement: Contract Query and Discovery

The system SHALL allow consumers to query and list contracts, supporting optional filtering by active status and associated supplier.

#### Scenario: List all active contracts by default

- **GIVEN** registered active and inactive vendor contracts in the system
- **WHEN** a consumer requests the contracts list without explicit filters
- **THEN** the system returns only active contracts with their code, title, supplier ID, and default allocation shares

#### Scenario: Filter contracts by specific supplier

- **GIVEN** contracts registered across multiple suppliers
- **WHEN** a consumer queries contracts filtering by a specific supplier UUID
- **THEN** the system returns only contracts belonging to that supplier

#### Scenario: Include inactive contracts when explicitly requested

- **GIVEN** active and inactive contracts exist
- **WHEN** a consumer queries contracts with active_only flag set to false
- **THEN** the system returns both active and deactivated contracts

### Requirement: Financial Measurement Query and Filtering

The system SHALL allow consumers to query and list financial measurements, supporting optional filtering by fiscal period, contract identifier, and lifecycle state.

#### Scenario: List measurements filtered by fiscal period

- **GIVEN** measurements submitted across periods "2026-01", "2026-02", and "2026-03"
- **WHEN** a consumer queries measurements for period "2026-03"
- **THEN** the system returns all measurements belonging to "2026-03" with their monetary amounts, states, and allocation entries

#### Scenario: Filter measurements by contract and lifecycle state

- **GIVEN** measurements in DRAFT, SUBMITTED, and APPROVED states for contract "CT-AWS-2026"
- **WHEN** a consumer queries measurements for that contract filtered by state "APPROVED"
- **THEN** the system returns only approved measurements associated with the specified contract

#### Scenario: Return empty list when no measurements match criteria

- **GIVEN** an active contract with no measurements recorded for period "2026-12"
- **WHEN** a consumer queries measurements matching that contract and period
- **THEN** the system returns an empty list without raising an error

### Requirement: Accounting Account Registration and Management

The system SHALL register and query accounting accounts defined by a standardized hierarchical code, friendly name, and active status.

#### Scenario: Register valid accounting account

- **WHEN** a user registers an accounting account with code "3.1.01", name "Licenciamento de Software", and description "Licenças SaaS e On-Premises"
- **THEN** the system persists the account as ACTIVE with a unique identifier and normalized account code

#### Scenario: Reject duplicate accounting account code

- **WHEN** a user attempts to register an accounting account with an existing code "3.1.01"
- **THEN** the system rejects registration with a duplicate entity error

#### Scenario: Reject invalid accounting account code syntax

- **WHEN** a user registers an account with code containing invalid characters or malformed hierarchy "3..1"
- **THEN** the system rejects registration with an invalid value object error

### Requirement: Measurement Allocation by Cost Center and Accounting Account

The system SHALL allow measurement cost distribution across combinations of Cost Center and Accounting Account while preserving 100% allocation summation and exact-penny reconciliation.

#### Scenario: Submit measurement with multi-account breakdown per cost center

- **WHEN** a measurement of $10,000.00 allocates 60% ($6,000.00) to Cost Center "1.1" under Account "3.1.01" (Software) and 40% ($4,000.00) to Cost Center "1.1" under Account "3.1.02" (Cloud Infrastructure)
- **THEN** the system accepts the measurement and records the distinct accounting account breakdown

#### Scenario: Reject allocation entry with inactive accounting account

- **WHEN** submitting a measurement linking an allocation entry to an INACTIVE accounting account
- **THEN** the system rejects the allocation entry with a domain rule violation

### Requirement: Cost Center Expenditure Breakdown by Accounting Account

The system SHALL provide an aggregated expenditure breakdown for any specified Cost Center and period, grouping all approved allocations by their associated Accounting Accounts.

#### Scenario: Retrieve accounting breakdown for cost center in period

- **WHEN** an analyst queries the accounting breakdown for Cost Center "1.1" in period "2026-03"
- **THEN** the system returns each accounting account's total spent amount, percentage share within the cost center, and the list of contributing contract measurements

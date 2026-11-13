# cost-allocation Specification Delta: Accounting Accounts Breakdown

## Purpose

Enables granular expense classification by associating cost allocation entries with specific Accounting Accounts (Contas Contábeis) within Cost Centers.

## ADDED Requirements

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

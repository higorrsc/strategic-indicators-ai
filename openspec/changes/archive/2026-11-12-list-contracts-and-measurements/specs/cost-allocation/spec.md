# Spec Delta: cost-allocation

## ADDED Requirements

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

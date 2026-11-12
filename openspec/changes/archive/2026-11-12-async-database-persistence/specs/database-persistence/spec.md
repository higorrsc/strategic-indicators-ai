# Spec Delta: Asynchronous Database Persistence

## Purpose

Provides durable, asynchronous relational database storage, transaction boundaries, and schema migrations for enterprise financial entities across budgeting and cost allocation contexts.

## ADDED Requirements

### Requirement: Asynchronous Multi-Database Engine Configuration

The system SHALL provide an asynchronous database connection factory that supports PostgreSQL for containerized environments and in-memory SQLite for automated testing.

#### Scenario: Production PostgreSQL connection setup

- **GIVEN** the application environment specifies a PostgreSQL connection string
- **WHEN** the database session factory initializes
- **THEN** it SHALL establish an asynchronous engine using asyncpg driver and pool connections

#### Scenario: Testing SQLite in-memory setup

- **GIVEN** the application environment specifies an in-memory SQLite connection string
- **WHEN** the test harness initializes the database session
- **THEN** it SHALL establish an isolated asynchronous SQLite engine using aiosqlite without requiring external database processes

### Requirement: Database Migration Lifecycle Management

The system SHALL manage relational schema versioning and execution through asynchronous Alembic migrations.

#### Scenario: Migration execution on startup

- **WHEN** database migration commands or application startup migration hooks execute
- **THEN** the system SHALL apply all unapplied migration revisions asynchronously up to the head revision

#### Scenario: Schema validation and rollback capability

- **WHEN** a migration revision fails during execution
- **THEN** the database transaction SHALL roll back, preventing partial schema corruption

### Requirement: Asynchronous Domain Entity Persistence

The system SHALL persist and retrieve domain aggregates across Budgeting and Cost Allocation bounded contexts through asynchronous SQLAlchemy repositories without leaking ORM models into the domain.

#### Scenario: Cost center hierarchy persistence

- **GIVEN** a new cost center aggregate with an optional parent relationship
- **WHEN** the cost center repository persists the aggregate
- **THEN** it SHALL asynchronously store the record and reconstitute the exact domain entity with parent-child invariants on retrieval

#### Scenario: Budget target persistence

- **GIVEN** a valid budget target defined for a cost center and period
- **WHEN** the budget repository persists or queries targets
- **THEN** it SHALL persist non-negative monetary amounts and retrieve them as strongly typed Money value objects

#### Scenario: Contract and measurement allocation persistence

- **GIVEN** an approved measurement containing exact-penny allocation entries
- **WHEN** the measurement repository saves the aggregate
- **THEN** all associated allocation line items SHALL be stored transactionally and reconciled with zero penny leakage

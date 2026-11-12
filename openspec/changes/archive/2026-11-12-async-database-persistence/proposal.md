# Proposal: Asynchronous Database Persistence with SQLAlchemy and Alembic

## Why

Currently, the application stores domain aggregates and entities in transient in-memory repository doubles. To support production deployment, enterprise data durability, transaction consistency, and multi-tenant scaling, the application requires a persistent relational database layer.

This change introduces asynchronous database persistence using SQLAlchemy 2.0 and Alembic for automated database migrations, backed by PostgreSQL in Docker Compose for production and development, and SQLite in-memory for fast, isolated automated tests.

## What Changes

- Add production and development database dependencies (`sqlalchemy>=2.0.36`, `asyncpg>=0.30.0`, `alembic>=1.14.0`, `aiosqlite>=0.20.0`).
- Configure Docker Compose orchestrating both the PostgreSQL 16 database service with persistent volume and the FastAPI ASGI application service.
- Implement central asynchronous database engine, session management, and Unit of Work / transaction lifecycle in `src/shared/infrastructure/database/`.
- Setup Alembic migration environment with async migration runner and autogenerate support.
- Implement SQLAlchemy ORM models and asynchronous repositories context by context:
  - Phase 1: Budgeting Bounded Context (`CostCenterModel`, `BudgetTargetModel`, `SqlAlchemyCostCenterRepository`, `SqlAlchemyBudgetRepository`).
  - Phase 2: Cost Allocation Bounded Context (`SupplierModel`, `ContractModel`, `ContractAllocationModel`, `MeasurementModel`, `AllocationEntryModel`, repositories).
- Update dependency injection composition root in `src/presentation/dependencies.py` to provide asynchronous database sessions and repositories, with configurable database URL.
- Support in-memory SQLite (`sqlite+aiosqlite:///:memory:`) for automated test suite execution without external database dependencies.

## Capabilities

### New Capabilities

- `database-persistence`: Asynchronous relational persistence and migration infrastructure supporting PostgreSQL and SQLite with SQLAlchemy ORM models, transaction management, and Alembic migrations across all bounded contexts.

### Modified Capabilities

None. Existing domain behaviors and API contracts remain identical, adhering to Clean Architecture repository interfaces.

## Impact

- **Dependencies**: Adds `sqlalchemy`, `asyncpg`, `alembic`, `aiosqlite` to project dependencies.
- **Infrastructure**: Adds `docker-compose.yml`, `Dockerfile`, `alembic.ini`, and `migrations/` directory.
- **Architecture**: Implements concrete database repositories in `src/budgeting/infrastructure/repositories/` and `src/allocation/infrastructure/repositories/`, mapping domain entities to ORM models without ORM leakage into the domain.
- **Testing**: Integrates in-memory asynchronous SQLite test fixtures in `conftest.py` ensuring all unit, API, and BDD test suites pass without a live Postgres instance.

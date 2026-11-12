# Design: Asynchronous Database Persistence Architecture

## Context

The system's core business logic is encapsulated in pure domain entities and use cases depending on repository protocols (`CostCenterRepository`, `BudgetRepository`, `SupplierRepository`, `ContractRepository`, `MeasurementRepository`). Currently, repository interfaces are satisfied by in-memory test doubles (`src/budgeting/infrastructure/repositories/in_memory_budgeting_repository.py` and `src/allocation/infrastructure/repositories/in_memory_allocation_repository.py`).

See `proposal.md` for motivation and scope.

## Goals / Non-Goals

**Goals:**

- Provide asynchronous relational persistence using SQLAlchemy 2.0 (`AsyncSession`, `async_sessionmaker`, `create_async_engine`).
- Support PostgreSQL 16 via `asyncpg` for containerized and production deployments.
- Support in-memory SQLite via `aiosqlite` for fast, zero-dependency unit and BDD tests.
- Manage database schema migrations through Alembic with an async migration runner.
- Dockerize the solution with `docker-compose.yml` orchestrating PostgreSQL and the FastAPI application.
- Preserve Clean Architecture boundaries: ORM models remain in infrastructure; domain aggregates are mapped to and from ORM models inside repositories.

**Non-Goals:**

- No synchronous database access.
- No direct exposure of SQLAlchemy ORM models or sessions to use cases or presentation controllers.
- No distributed transactions or multi-database two-phase commit protocols.

## Decisions

### 1. Database Engine & Session Management

- **Decision**: Centralize asynchronous engine creation in `src/shared/infrastructure/database/session.py`.
- **Rationale**: Keeps database connection parameters, pooling, and session factory unified.
- **Alternatives Considered**: Creating independent engines per bounded context (rejected due to connection exhaustion and inability to share transactions when needed).

### 2. ORM Modeling & Domain Entity Isolation

- **Decision**: Define separate SQLAlchemy models in infrastructure:
  - Budgeting Context (`src/budgeting/infrastructure/database/models.py`): `CostCenterModel`, `BudgetTargetModel`.
  - Allocation Context (`src/allocation/infrastructure/database/models.py`): `SupplierModel`, `ContractModel`, `ContractAllocationModel`, `MeasurementModel`, `AllocationEntryModel`.
- **Rationale**: Adheres to `AGENTS.md` (Domain MUST NOT depend on SQLAlchemy; Domain Entity $\neq$ SQLAlchemy Model). Repositories map domain aggregates to ORM models on write and reconstitute rich domain aggregates on read.
- **Alternatives Considered**: Directly annotating domain entities with SQLAlchemy dataclass / mapped columns (rejected because it pollutes domain with database annotations and lifecycle hooks).

### 3. Cross-Dialect Portability (PostgreSQL & SQLite)

- **Decision**: Use generic SQLAlchemy types compatible with both PostgreSQL and SQLite:
  - Primary keys: `Uuid(as_uuid=True)` or `String(36)` with automated UUID conversion.
  - Monetary values: `Numeric(18, 2)` mapping to Python `Decimal` and `Money`.
  - Percentages: `Numeric(7, 4)` mapping to Python `Decimal` and `Percentage`.
  - Dates/Periods: `String(7)` (e.g. `YYYY-MM`) mapping to `Period`.
- **Rationale**: Ensures identical behavior across containerized PostgreSQL (`asyncpg`) and test-suite in-memory SQLite (`aiosqlite`).
- **Alternatives Considered**: PostgreSQL-specific types like `UUID` or `JSONB` (rejected because they break in SQLite in-memory testing).

### 4. Phased Repository Migration & Dependency Injection

- **Decision**: Implement repositories in phased stages:
  - Phase 1: Budgeting Bounded Context repositories.
  - Phase 2: Cost Allocation Bounded Context repositories.
  Update `src/presentation/dependencies.py` to inject database-backed repositories when `DATABASE_URL` is configured, while allowing in-memory substitution via `DependencyContainer`.
- **Rationale**: Allows incremental verification and testing of each context without breaking existing capabilities.

### 5. Alembic Asynchronous Migration Runner

- **Decision**: Configure `alembic` with `env.py` running in async mode using `async_engine_from_config` and `run_sync`.
- **Rationale**: Native integration with SQLAlchemy 2.0 async engine and metadata autogeneration across all bounded context models.

### 6. Containerization (Docker Compose)

- **Decision**: Provide a multi-stage `Dockerfile` and `docker-compose.yml` with:
  - `db`: `postgres:16-alpine` with healthcheck (`pg_isready`), persistent volume, and environment credentials.
  - `app`: FastAPI ASGI application depending on `db` health, running migrations on startup before serving HTTP.

## Risks / Trade-offs

- **[Risk] SQLite in-memory multi-connection concurrency**: In-memory SQLite creates a new empty database per connection unless configured with a shared pool.
  &rarr; *Mitigation*: Configure SQLite in-memory test engines with `StaticPool` and `check_same_thread=False` to share the in-memory database across async test tasks.
- **[Risk] Foreign key constraints across bounded contexts**: Measurement allocation entries reference cost center IDs across context boundaries.
  &rarr; *Mitigation*: In the allocation context, store `cost_center_id` as an indexed UUID without cross-context table foreign key constraints, preserving bounded context independence.
- **[Risk] Nested relationship lazy-loading exceptions**: Accessing un-eagerly loaded relationships in async SQLAlchemy triggers `MissingGreenlet` errors.
  &rarr; *Mitigation*: Always use explicit eager loading (`selectinload`) in repositories when querying contracts with allocations and measurements with entries.

## Migration Plan

1. Ingest database dependencies (`sqlalchemy`, `asyncpg`, `alembic`, `aiosqlite`) via `uv`.
2. Configure settings with `DATABASE_URL` defaulting to PostgreSQL for local dev and SQLite for tests.
3. Author initial Alembic migration creating budgeting and allocation schema tables.
4. Verify all automated tests pass using async SQLite in-memory engine before running Docker Compose with Postgres.

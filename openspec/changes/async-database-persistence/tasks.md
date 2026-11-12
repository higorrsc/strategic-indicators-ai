# Tasks: Asynchronous Database Persistence with SQLAlchemy and Alembic

## 1. Database Dependencies & Core Async Infrastructure

- [x] 1.1 Ingest dependencies (`sqlalchemy>=2.0.36`, `asyncpg>=0.30.0`, `alembic>=1.14.0`, `aiosqlite>=0.20.0`) in `pyproject.toml` and verify with `uv sync`
- [x] 1.2 Update application settings with `DATABASE_URL` in `src/shared/config/settings.py` and `.env.example`
- [x] 1.3 Implement centralized async database session manager and `BaseModel` declarative base in `src/shared/infrastructure/database/` and verify engine initialization
- [x] 1.4 Setup Alembic environment with async runner in `alembic.ini` and `migrations/env.py` and verify configuration

## 2. Budgeting Context Persistence (Phase 1)

- [x] 2.1 Implement SQLAlchemy ORM models (`CostCenterModel`, `BudgetTargetModel`) in `src/budgeting/infrastructure/database/models.py`
- [x] 2.2 Implement `SqlAlchemyCostCenterRepository` and `SqlAlchemyBudgetRepository` in `src/budgeting/infrastructure/repositories/`
- [x] 2.3 Write integration tests for Budgeting database repositories using async in-memory SQLite in `tests/integration/database/test_budgeting_persistence.py` and verify tests pass

## 3. Cost Allocation Context Persistence (Phase 2)

- [x] 3.1 Implement SQLAlchemy ORM models (`SupplierModel`, `ContractModel`, `ContractAllocationModel`, `MeasurementModel`, `AllocationEntryModel`) in `src/allocation/infrastructure/database/models.py`
- [x] 3.2 Implement `SqlAlchemySupplierRepository`, `SqlAlchemyContractRepository`, and `SqlAlchemyMeasurementRepository` in `src/allocation/infrastructure/repositories/`
- [x] 3.3 Write integration tests for Allocation database repositories using async in-memory SQLite in `tests/integration/database/test_allocation_persistence.py` and verify tests pass

## 4. Alembic Migrations & Schema Generation

- [ ] 4.1 Generate initial Alembic migration revision including all budgeting and cost allocation tables in `migrations/versions/`
- [ ] 4.2 Verify automated migration execution (`alembic upgrade head`) against async engine and confirm schema creation

## 5. Dependency Injection Wiring & Test Suite Adaptation

- [ ] 5.1 Update composition root in `src/presentation/dependencies.py` to instantiate and inject asynchronous database repositories
- [ ] 5.2 Adapt test fixtures in `tests/conftest.py`, `tests/api/conftest.py`, and `tests/bdd/conftest.py` to run seamlessly against async in-memory SQLite with schema setup
- [ ] 5.3 Execute complete test suite (`uv run pytest`) and verify all unit, API, and BDD tests pass against SQLite in-memory

## 6. Containerization with Docker Compose & PostgreSQL

- [ ] 6.1 Create multi-stage production `Dockerfile` for the FastAPI application with `uv`
- [ ] 6.2 Create `docker-compose.yml` with `db` (PostgreSQL 16 Alpine + healthcheck) and `app` (FastAPI + migration hook)
- [ ] 6.3 Verify docker compose configuration syntax with `docker compose config`

## 7. Quality Assurance & Static Verification

- [ ] 7.1 Run formatter (`uv run ruff format .`) and check style compliance
- [ ] 7.2 Run linter (`uv run ruff check .`) and resolve all warnings
- [ ] 7.3 Run static type checker (`uv run pyrefly check`) and confirm zero type errors
- [ ] 7.4 Execute complete test suite (`uv run pytest --cov=src`) confirming 100% pass and coverage thresholds

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived specifications in `openspec/specs/`.

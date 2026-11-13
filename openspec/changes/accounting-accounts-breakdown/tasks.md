# Tasks: Accounting Accounts Breakdown in Cost Allocation

- [x] 1. Domain Modeling & Value Objects
  - [x] 1.1 Create `AccountCode` value object with format validation and unit tests (`tests/unit/shared/test_value_objects.py`)
  - [x] 1.2 Create `AccountingAccount` domain entity with business methods (`tests/unit/allocation/test_accounting_account.py`)
  - [x] 1.3 Update `AllocationEntry` entity to include `accounting_account_id`
  - [x] 1.4 Define `AccountingAccountRepository` port interface in `src/domain/allocation/repositories.py`

- [x] 2. Persistence & Migrations
  - [x] 2.1 Create SQLAlchemy ORM model `AccountingAccountModel` in `src/infrastructure/database/models/allocation.py`
  - [x] 2.2 Add `accounting_account_id` foreign key column to `allocation_entries` ORM model
  - [x] 2.3 Generate Alembic migration script in `src/infrastructure/database/migrations/versions/`
  - [x] 2.4 Implement `SqlAlchemyAccountingAccountRepository` in `src/infrastructure/database/repositories/accounting_account_repository.py`
  - [x] 2.5 Write integration repository tests in `tests/integration/database/test_accounting_account_persistence.py`

- [x] 3. Application Use Cases
  - [x] 3.1 Implement `RegisterAccountingAccountUseCase` with uniqueness validation
  - [x] 3.2 Implement `ListAccountingAccountsUseCase` supporting pagination
  - [x] 3.3 Implement `GetCostCenterAccountingBreakdownUseCase` aggregating spent amounts by accounting account
  - [x] 3.4 Update `SubmitMeasurementUseCase` to validate accounting account existence and active status
  - [x] 3.5 Write unit tests for all use cases in `tests/unit/allocation/`

- [x] 4. Presentation & API Layer
  - [x] 4.1 Define Pydantic request/response schemas in `src/presentation/schemas/accounting.py`
  - [x] 4.2 Create router `src/presentation/api/v1/accounting_router.py` with `POST` and `GET /api/v1/accounting-accounts`
  - [x] 4.3 Add endpoint `GET /api/v1/cost-centers/{cost_center_id}/accounting-breakdown`
  - [x] 4.4 Wire dependencies in `src/presentation/dependencies.py` and register router in `src/main.py`
  - [x] 4.5 Write API tests in `tests/api/test_api_accounting.py`

- [x] 5. Documentation & Verification
  - [x] 5.1 Run `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`
  - [x] 5.2 Update `README.md` and OpenAPI documentation

# CQRS Separation and Architectural Modularization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the codebase to separate Use Cases into `commands/` and `queries/` (CQRS), modularize high-density files (Allocation models, DTOs, routers, composition root dependencies, and seeding scripts), and symmetrically mirror the unit and API test suite according to Clean Architecture and DDD principles.

**Architecture:** Bounded contexts retain clean layer boundaries (Domain, Application, Infrastructure, Presentation). Application logic is segregated into CQRS `commands/` (mutations) and `queries/` (read/computations). Dense files are decomposed into cohesive subpackages by aggregate, while `SessionManaged*Repository` classes are co-located within each context's repository infrastructure. `tests/` mirrors `src/` 1:1.

**Tech Stack:** Python 3.15, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Pytest, Ruff, Pyrefly.

**Spec:** [`docs/superpowers/specs/2026-11-13-cqrs-and-modularization-refactoring-design.md`](docs/superpowers/specs/2026-11-13-cqrs-and-modularization-refactoring-design.md)

## Global Constraints

- Domain layer must remain pure Python with zero dependencies on frameworks, ORMs, or outer layers.
- Strict type checking compliance with Pyrefly: 0 errors, no unannotated definitions, no unnecessary `Any`.
- Code formatting and linting compliance with Ruff: line-length 88, 0 linter warnings.
- No legacy backwards-compatibility shims: directly update callers, routers, DI container, and tests to the canonical module paths.
- All 159 existing tests must pass after each task without breaking business logic, calculation precision, or HTTP contracts.

## Review Focus

1. **Alembic Table Discovery:** Moving `src/allocation/infrastructure/database/models.py` to `models/` subpackage must not alter `Base.metadata` table registrations or break Alembic imports.
2. **DI Container Facade Delegation:** `DependencyContainer` in `src/presentation/dependencies/container.py` must expose all existing property names and reset methods so test fixtures and API clients continue functioning seamlessly.
3. **Circular Import Prevention:** Subpackages (`models/`, `dto/`, `commands/`, `queries/`) must use clean relative or absolute imports without introducing circular dependencies.
4. **Router Route Invariants:** Splitting `allocation_router.py` into `contracts_router.py` and `measurements_router.py` must preserve exact HTTP paths (`/api/v1/contracts`, `/api/v1/measurements`, etc.) and status codes.
5. **Test Discovery Completeness:** Mirroring `tests/unit/` and `tests/api/` must retain all test functions and test markers (`@pytest.mark.asyncio`), maintaining identical test count.

---

### Task 1: Budgeting & Indicators CQRS Separation & Test Mirroring

**Files:**
- Create:
  - `src/budgeting/application/commands/__init__.py`
  - `src/budgeting/application/commands/create_cost_center.py`
  - `src/budgeting/application/commands/set_budget_target.py`
  - `src/budgeting/application/queries/__init__.py`
  - `src/budgeting/application/queries/get_hierarchy_budget.py`
  - `src/indicators/application/queries/__init__.py`
  - `src/indicators/application/queries/compute_period_indicators.py`
  - `src/indicators/application/queries/material_impact.py`
  - `src/indicators/application/queries/simulate_scenario.py`
  - `tests/unit/budgeting/domain/test_cost_center.py`
  - `tests/unit/budgeting/domain/test_budget_target.py`
  - `tests/unit/budgeting/application/commands/test_create_cost_center.py`
  - `tests/unit/budgeting/application/commands/test_set_budget_target.py`
  - `tests/unit/budgeting/application/queries/test_get_hierarchy_budget.py`
  - `tests/unit/indicators/domain/test_variance_calculator.py`
  - `tests/unit/indicators/domain/test_simulator.py`
  - `tests/unit/indicators/domain/test_materiality_analyzer.py`
  - `tests/unit/indicators/application/queries/test_compute_period_indicators.py`
  - `tests/unit/indicators/application/queries/test_simulate_scenario.py`
  - `tests/unit/indicators/application/queries/test_material_impact.py`
- Delete:
  - `src/budgeting/application/use_cases/`
  - `src/indicators/application/use_cases/`
  - `tests/unit/budgeting/test_budgeting.py`
  - `tests/unit/indicators/test_indicators.py`
  - `tests/unit/indicators/test_material_impact_use_case.py`
  - `tests/unit/indicators/test_materiality_analyzer.py`

**Interfaces:**
- Produces:
  - `src.budgeting.application.commands: CreateCostCenterUseCase, SetBudgetTargetUseCase`
  - `src.budgeting.application.queries: GetHierarchyBudgetUseCase`
  - `src.indicators.application.queries: ComputePeriodIndicatorsUseCase, SimulateScenarioUseCase, MaterialImpactUseCase`

- [ ] **Step 1: Move budgeting and indicators use cases into `commands/` and `queries/`**
Move files and adjust `__init__.py` in `src/budgeting/application/` and `src/indicators/application/`. Remove the old `use_cases/` directories.

- [ ] **Step 2: Update references in presentation routers and dependencies**
Update import statements in `src/presentation/api/v1/budgeting_router.py`, `src/presentation/api/v1/indicators_router.py`, and `src/presentation/dependencies.py` to import from `commands` and `queries`.

- [ ] **Step 3: Restructure budgeting and indicators unit tests to mirror src structure**
Split `test_budgeting.py` into `domain/test_cost_center.py`, `domain/test_budget_target.py`, `application/commands/test_create_cost_center.py`, `application/commands/test_set_budget_target.py`, `application/queries/test_get_hierarchy_budget.py`.
Split indicators tests into `domain/` and `application/queries/`.

- [ ] **Step 4: Run pytest and linters on budgeting and indicators**
Run: `uv run pytest tests/unit/budgeting/ tests/unit/indicators/ -v`
Expected: All tests pass.
Run: `uv run ruff check src/budgeting src/indicators tests/unit/budgeting tests/unit/indicators && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 5: Commit**
```bash
git add src/budgeting/ src/indicators/ src/presentation/ tests/unit/budgeting/ tests/unit/indicators/
git commit -m "♻️ refactor(budgeting,indicators): separate use cases into commands and queries and mirror test suite"
```

---

### Task 2: Allocation Models, DTOs & CQRS Separation & Test Mirroring

**Files:**
- Create:
  - `src/allocation/infrastructure/database/models/__init__.py`
  - `src/allocation/infrastructure/database/models/supplier.py`
  - `src/allocation/infrastructure/database/models/contract.py`
  - `src/allocation/infrastructure/database/models/measurement.py`
  - `src/allocation/infrastructure/database/models/accounting_account.py`
  - `src/allocation/application/dto/__init__.py`
  - `src/allocation/application/dto/supplier.py`
  - `src/allocation/application/dto/contract.py`
  - `src/allocation/application/dto/measurement.py`
  - `src/allocation/application/dto/accounting.py`
  - `src/allocation/application/commands/__init__.py`
  - `src/allocation/application/commands/register_accounting_account.py`
  - `src/allocation/application/commands/register_contract.py`
  - `src/allocation/application/commands/submit_measurement.py`
  - `src/allocation/application/commands/approve_measurement.py`
  - `src/allocation/application/queries/__init__.py`
  - `src/allocation/application/queries/list_accounting_accounts.py`
  - `src/allocation/application/queries/list_contracts.py`
  - `src/allocation/application/queries/list_measurements.py`
  - `src/allocation/application/queries/get_cost_center_accounting_breakdown.py`
  - `tests/unit/allocation/domain/test_exact_penny_allocator.py`
  - `tests/unit/allocation/domain/test_contract.py`
  - `tests/unit/allocation/domain/test_measurement.py`
  - `tests/unit/allocation/domain/test_accounting_account.py`
  - `tests/unit/allocation/application/commands/test_register_contract.py`
  - `tests/unit/allocation/application/commands/test_submit_measurement.py`
  - `tests/unit/allocation/application/commands/test_approve_measurement.py`
  - `tests/unit/allocation/application/commands/test_register_accounting_account.py`
  - `tests/unit/allocation/application/queries/test_list_contracts.py`
  - `tests/unit/allocation/application/queries/test_list_measurements.py`
  - `tests/unit/allocation/application/queries/test_list_accounting_accounts.py`
  - `tests/unit/allocation/application/queries/test_get_cost_center_accounting_breakdown.py`
- Delete:
  - `src/allocation/infrastructure/database/models.py`
  - `src/allocation/application/dto.py`
  - `src/allocation/application/use_cases/`
  - `tests/unit/allocation/test_allocation.py`
  - `tests/unit/allocation/test_accounting_account.py`
  - `tests/unit/allocation/test_accounting_use_cases.py`

**Interfaces:**
- Produces:
  - `src.allocation.infrastructure.database.models: SupplierModel, ContractModel, ContractAllocationModel, MeasurementModel, AllocationEntryModel, AccountingAccountModel`
  - `src.allocation.application.dto: SupplierDTO, ContractDTO, ContractCreateDTO, DefaultAllocationDTO, MeasurementDTO, MeasurementSubmitDTO, AllocationEntryDTO, AccountingAccountDTO, AccountingAccountCreateDTO, CostCenterAccountSpendDTO`
  - `src.allocation.application.commands: RegisterAccountingAccountUseCase, RegisterContractUseCase, SubmitMeasurementUseCase, ApproveMeasurementUseCase`
  - `src.allocation.application.queries: ListAccountingAccountsUseCase, ListContractsUseCase, ListMeasurementsUseCase, GetCostCenterAccountingBreakdownUseCase`

- [ ] **Step 1: Modularize `src/allocation/infrastructure/database/models/`**
Split `models.py` into `supplier.py`, `contract.py`, `measurement.py`, `accounting_account.py`. Re-export all in `models/__init__.py`. Delete `models.py`.

- [ ] **Step 2: Modularize `src/allocation/application/dto/`**
Split `dto.py` into `supplier.py`, `contract.py`, `measurement.py`, `accounting.py`. Re-export all in `dto/__init__.py`. Delete `dto.py`.

- [ ] **Step 3: Move allocation use cases to `commands/` and `queries/`**
Move files and update `src/allocation/application/__init__.py`. Delete `src/allocation/application/use_cases/`.

- [ ] **Step 4: Update presentation and repository references**
Update imports in `src/allocation/infrastructure/repositories/`, `src/presentation/api/v1/allocation_router.py`, `src/presentation/api/v1/accounting_router.py`, and `src/presentation/dependencies.py`.

- [ ] **Step 5: Restructure allocation unit tests to mirror src structure**
Decompose `test_allocation.py`, `test_accounting_account.py`, and `test_accounting_use_cases.py` into `tests/unit/allocation/domain/` and `tests/unit/allocation/application/` (`commands/` and `queries/`).

- [ ] **Step 6: Run pytest and linters on allocation**
Run: `uv run pytest tests/unit/allocation/ tests/integration/database/ -v`
Expected: All tests pass.
Run: `uv run ruff check src/allocation tests/unit/allocation && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 7: Commit**
```bash
git add src/allocation/ src/presentation/ tests/unit/allocation/
git commit -m "♻️ refactor(allocation): modularize models, dtos, use cases (CQRS) and mirror tests"
```

---

### Task 3: Intelligence CQRS Separation & Test Mirroring

**Files:**
- Create:
  - `src/intelligence/application/queries/__init__.py`
  - `src/intelligence/application/queries/analyze_allocation_anomalies.py`
  - `src/intelligence/application/queries/generate_executive_summary.py`
  - `tests/unit/intelligence/domain/test_anomaly_detector.py`
  - `tests/unit/intelligence/domain/test_cache_domain.py`
  - `tests/unit/intelligence/application/services/test_data_fingerprint_service.py`
  - `tests/unit/intelligence/application/queries/test_analyze_allocation_anomalies.py`
  - `tests/unit/intelligence/application/queries/test_executive_summary_caching.py`
- Delete:
  - `src/intelligence/application/use_cases/`
  - `tests/unit/intelligence/test_cache_domain.py`
  - `tests/unit/intelligence/test_data_fingerprint_service.py`
  - `tests/unit/intelligence/test_executive_summary_caching.py`
  - `tests/unit/intelligence/test_intelligence.py`

**Interfaces:**
- Produces:
  - `src.intelligence.application.queries: AnalyzeAllocationAnomaliesUseCase, GenerateExecutiveSummaryUseCase`

- [ ] **Step 1: Move intelligence use cases to `src/intelligence/application/queries/`**
Move files and adjust `src/intelligence/application/__init__.py`. Delete `src/intelligence/application/use_cases/`.

- [ ] **Step 2: Update presentation references**
Update imports in `src/presentation/api/v1/intelligence_router.py` and `src/presentation/dependencies.py`.

- [ ] **Step 3: Restructure intelligence unit tests to mirror src structure**
Reorganize `test_intelligence.py`, `test_cache_domain.py`, `test_data_fingerprint_service.py`, `test_executive_summary_caching.py` into `tests/unit/intelligence/domain/` and `tests/unit/intelligence/application/` (`services/` and `queries/`).

- [ ] **Step 4: Run pytest and linters on intelligence**
Run: `uv run pytest tests/unit/intelligence/ tests/integration/intelligence/ -v`
Expected: All tests pass.
Run: `uv run ruff check src/intelligence tests/unit/intelligence && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 5: Commit**
```bash
git add src/intelligence/ src/presentation/ tests/unit/intelligence/
git commit -m "♻️ refactor(intelligence): separate use cases into queries and mirror test suite"
```

---

### Task 4: Co-Location of Session-Managed Repositories

**Files:**
- Create:
  - `src/budgeting/infrastructure/repositories/session_managed.py`
  - `src/allocation/infrastructure/repositories/session_managed.py`
  - `src/intelligence/infrastructure/repositories/session_managed.py`
- Modify:
  - `src/budgeting/infrastructure/repositories/__init__.py`
  - `src/allocation/infrastructure/repositories/__init__.py`
  - `src/intelligence/infrastructure/repositories/__init__.py`
- Delete:
  - `src/shared/infrastructure/database/repositories.py`

**Interfaces:**
- Produces:
  - `src.budgeting.infrastructure.repositories.session_managed: SessionManagedCostCenterRepository, SessionManagedBudgetTargetRepository`
  - `src.allocation.infrastructure.repositories.session_managed: SessionManagedSupplierRepository, SessionManagedContractRepository, SessionManagedMeasurementRepository, SessionManagedAccountingAccountRepository`
  - `src.intelligence.infrastructure.repositories.session_managed: SessionManagedAIAnalysisCacheRepository`

- [ ] **Step 1: Move session-managed repositories to their bounded context infrastructure folders**
Extract session-managed classes from `src/shared/infrastructure/database/repositories.py` into `src/budgeting/infrastructure/repositories/session_managed.py`, `src/allocation/infrastructure/repositories/session_managed.py`, and `src/intelligence/infrastructure/repositories/session_managed.py`.
Delete `src/shared/infrastructure/database/repositories.py`.

- [ ] **Step 2: Update references in dependencies and presentation**
Update imports in `src/presentation/dependencies.py` to point to the context-specific session-managed repositories.

- [ ] **Step 3: Run pytest and linters**
Run: `uv run pytest tests/integration/ tests/api/ -v`
Expected: All tests pass.
Run: `uv run ruff check src/ && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 4: Commit**
```bash
git add src/budgeting/ src/allocation/ src/intelligence/ src/shared/ src/presentation/
git commit -m "♻️ refactor(persistence): co-locate session-managed repositories in bounded contexts"
```

---

### Task 5: Modular Composition Root (`src/presentation/dependencies/`)

**Files:**
- Create:
  - `src/presentation/dependencies/__init__.py`
  - `src/presentation/dependencies/container.py`
  - `src/presentation/dependencies/database.py`
  - `src/presentation/dependencies/budgeting.py`
  - `src/presentation/dependencies/allocation.py`
  - `src/presentation/dependencies/indicators.py`
  - `src/presentation/dependencies/intelligence.py`
- Delete:
  - `src/presentation/dependencies.py`

**Interfaces:**
- Produces:
  - `src.presentation.dependencies: get_container, set_container, reset_container, DependencyContainer`

- [ ] **Step 1: Decompose dependencies into context modules**
Create `database.py` (engine & session factory lifecycle), `budgeting.py` (providers for budgeting), `allocation.py` (providers for allocation), `indicators.py` (providers for indicators), and `intelligence.py` (providers for intelligence & AI port).

- [ ] **Step 2: Build `DependencyContainer` facade in `container.py`**
Assemble the modules into `container.py` exposing identical public properties (`create_cost_center_use_case`, `ai_port`, `init_database`, etc.).
Expose `get_container()`, `set_container()`, `reset_container()`, and `DependencyContainer` in `dependencies/__init__.py`. Delete `dependencies.py`.

- [ ] **Step 3: Run full test suite to verify DI facade integrity**
Run: `uv run pytest -v`
Expected: All 159 tests pass.
Run: `uv run ruff check src/presentation/dependencies && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 4: Commit**
```bash
git add src/presentation/dependencies/
git commit -m "♻️ refactor(presentation): modularize dependency injection container by context"
```

---

### Task 6: Modular Routers & API Tests Mirroring

**Files:**
- Create:
  - `src/presentation/api/v1/contracts_router.py`
  - `src/presentation/api/v1/measurements_router.py`
  - `tests/api/test_contracts_api.py`
  - `tests/api/test_measurements_api.py`
  - `tests/api/test_indicators_api.py`
  - `tests/api/test_scenarios_api.py`
  - `tests/api/test_intelligence_api.py`
- Modify:
  - `src/presentation/api/v1/__init__.py`
  - `src/presentation/app.py`
- Delete:
  - `src/presentation/api/v1/allocation_router.py`
  - `tests/api/test_api_allocation.py`
  - `tests/api/test_api_indicators_and_intelligence.py`
  - `tests/api/test_intelligence_caching_api.py`

**Interfaces:**
- Produces:
  - `src.presentation.api.v1.contracts_router: router as contracts_router`
  - `src.presentation.api.v1.measurements_router: router as measurements_router`

- [ ] **Step 1: Split `allocation_router.py` into `contracts_router.py` and `measurements_router.py`**
Separate contract endpoints from measurement endpoints. Mount both in `src/presentation/app.py` and export in `src/presentation/api/v1/__init__.py`. Delete `allocation_router.py`.

- [ ] **Step 2: Split API tests to mirror modular routers**
Split `test_api_allocation.py` into `test_contracts_api.py` and `test_measurements_api.py`.
Split `test_api_indicators_and_intelligence.py` and `test_intelligence_caching_api.py` into `test_indicators_api.py`, `test_scenarios_api.py`, and `test_intelligence_api.py`.

- [ ] **Step 3: Run API test suite**
Run: `uv run pytest tests/api/ -v`
Expected: All API tests pass.
Run: `uv run ruff check src/presentation tests/api && uv run pyrefly check`
Expected: 0 errors.

- [ ] **Step 4: Commit**
```bash
git add src/presentation/api/v1/ tests/api/ src/presentation/app.py
git commit -m "♻️ refactor(api): split allocation router into contracts and measurements and mirror API tests"
```

---

### Task 7: Modular Seeding Scripts & Verification

**Files:**
- Create:
  - `scripts/seed/__init__.py`
  - `scripts/seed/data.py`
  - `scripts/seed/seeder.py`
  - `scripts/seed/runner.py`
- Modify:
  - `scripts/seed_ai_data.py`
  - `tests/integration/test_ai_agent_seed.py`

**Interfaces:**
- Produces:
  - `scripts.seed.data: CostCenterSeedData, ContractSeedData, MeasurementSeedData, build_seed_dataset`
  - `scripts.seed.seeder: seed_database`
  - `scripts.seed.runner: run_seed_and_analysis`

- [ ] **Step 1: Modularize `scripts/seed/`**
Extract dataset definitions into `data.py`, database persistence actions into `seeder.py`, and orchestration/analysis execution into `runner.py`. Make `scripts/seed_ai_data.py` a thin CLI wrapper calling `runner.run_seed_and_analysis`.

- [ ] **Step 2: Update `tests/integration/test_ai_agent_seed.py`**
Verify the seed integration test continues to pass against the modularized script.

- [ ] **Step 3: Run full verification suite**
Run:
```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
AI_PROVIDER=fake uv run python -m scripts.seed_ai_data --database-url "sqlite+aiosqlite:///:memory:" --clean
```
Expected: All 159 tests pass, 0 ruff errors, 355+ files formatted, 0 pyrefly errors, seed script runs successfully.

- [ ] **Step 4: Commit**
```bash
git add scripts/ tests/integration/test_ai_agent_seed.py
git commit -m "♻️ refactor(scripts): modularize synthetic financial data seeding workflow"
```

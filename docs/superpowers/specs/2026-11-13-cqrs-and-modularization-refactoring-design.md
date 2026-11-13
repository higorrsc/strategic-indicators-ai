# Design Document: CQRS Separation and Architectural Modularization

**Date:** 2026-11-13
**Status:** In Review
**Branch:** `feature/refactor-cqrs-and-modularization`

---

## 1. Intent and Context

The codebase has evolved rapidly into a feature-complete system following Clean Architecture and Domain-Driven Design (DDD). However, as new capabilities were added (such as AI analysis caching, multi-provider summaries, and accounting account breakdowns), several files and scripts accumulated excessive density and mixed multiple concerns:

1. **Use Cases Lack Intent Separation:** In each bounded context (`budgeting`, `allocation`, `indicators`, `intelligence`), use cases are mixed together in a flat `use_cases/` directory without clear distinction between state-mutating commands and read-only queries (CQRS principle).
2. **"God Container" in Presentation:** `src/presentation/dependencies.py` (771 lines) instantiates and manages session lifecycles for every repository, adapter, and use case across all bounded contexts in a monolithic class.
3. **Misplaced Infrastructure Repositories:** `src/shared/infrastructure/database/repositories.py` (341 lines) houses `SessionManaged*Repository` classes for all contexts in a shared global module instead of placing them within their respective bounded contexts.
4. **Monolithic Routers:** `src/presentation/api/v1/allocation_router.py` (474 lines) mixes endpoints for contracts, default allocations, measurements, approvals, and accounting breakdowns into a single file.
5. **Clustered Models and DTOs:** In `src/allocation/infrastructure/database/models.py` (170 lines) and `src/allocation/application/dto.py` (162 lines), multiple distinct aggregates (`Supplier`, `Contract`, `Measurement`, `AccountingAccount`) are bundled into single files.
6. **Monolithic Seeding Script:** `scripts/seed_ai_data.py` (639 lines) combines CLI arguments, database initialization, synthetic financial data generation, multi-stage seeding, anomaly verification, and executive AI summary invocation into one continuous script.

The goal of this refactoring is to untangle these concerns, increase cohesion, lower cognitive load, and make future maintenance effortless, while strictly preserving 100% test coverage and existing behavioral contracts.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals

- **CQRS Organization:** Separate use cases in all bounded contexts into explicit `commands/` and `queries/` subpackages.
- **Modular Composition Root:** Break down `src/presentation/dependencies.py` into cohesive context providers (e.g., `budgeting_container.py`, `allocation_container.py`, `intelligence_container.py`, coordinated by a slim container facade).
- **Context-Co-Located Repositories:** Move `SessionManaged*Repository` classes from `src/shared/` into their respective bounded contexts (e.g., `src/budgeting/infrastructure/repositories/session_managed.py`).
- **Cohesive Routers:** Split `src/presentation/api/v1/allocation_router.py` into focused sub-routers (`contracts_router.py`, `measurements_router.py`, keeping `accounting_router.py` distinct) and group them cleanly in `api/v1/`.
- **Modular Models and DTOs:** Split multi-aggregate `models.py` and `dto.py` in `allocation` into subpackages organized by aggregate, preserving public exports via package `__init__.py`.
- **Modular Seeding Scripts:** Decompose `scripts/seed_ai_data.py` into reusable modules (data definitions vs. execution workflow).
- **Zero Regressions:** Ensure all 159 tests pass, Ruff formatting and linting pass with 0 warnings, and Pyrefly passes with 0 typing errors.

### Non-Goals

- Altering business logic, calculation algorithms, rounding rules, or domain validation invariants.
- Modifying HTTP API endpoint paths, JSON request/response contracts, or query parameters.
- Changing database table schemas or generating new database migrations (ORM table names and columns remain identical).
- Introducing an asynchronous message bus or event-driven CQRS infrastructure (this refactoring is strictly architectural/structural separation of code responsibilities).

### Anti-Goals

- Creating legacy shim files or artificial backward-compatibility layers (since this is a new application, all imports in tests and presentation should be directly and cleanly refactored to the new canonical module paths).
- Creating deep unnecessary nesting or over-engineering abstractions just for the sake of separation.

---

## 3. Constraints

- **Clean Architecture & DDD (AGENTS.md):** Domain layer must remain pure Python with zero dependencies on frameworks, ORMs, or outer layers. Inner layers must not depend on outer layers.
- **Type Safety:** 100% strict typing compliance with Pyrefly (no unannotated definitions, no `Any` leaks).
- **Git Flow:** Feature developed on branch `feature/refactor-cqrs-and-modularization`.

---

## 4. Approaches Considered

### Approach 1: Modularization by Aggregate & CQRS (Selected)

- Replace flat `use_cases/` directories with explicit `commands/` and `queries/` subpackages in each bounded context, directly updating all callers and tests without legacy shims.
- Convert monolithic files (`models.py`, `dto.py`, `dependencies.py`, `repositories.py`, `allocation_router.py`, `seed_ai_data.py`) into cohesive modular subpackages or files.
- **Pros:** Directly eliminates files with 300-700+ lines, isolates single responsibilities, enhances readability, leaves zero technical debt or dead shim files.
- **Cons:** Requires updating import paths across the codebase and test files.

### Approach 2: Vertical Slice Re-Architecture (Rejected)

- Split the `allocation` context completely into three separate top-level bounded contexts (`src/contracts/`, `src/measurements/`, `src/accounting/`), each with its own domain, application, infrastructure, and presentation layers.
- **Pros:** Complete isolation of smaller subdomains.
- **Cons:** Drastic rewrite of the entire codebase structure, high overhead, high risk of regression, and artificial duplication of shared allocation infrastructure.

---

## 5. Detailed Structural Design

### 5.1 CQRS Separation in Application Layer

In each bounded context, the flat `use_cases/` directory is replaced by `commands/` and `queries/`:

```text
src/budgeting/application/
├── commands/
│   ├── __init__.py
│   ├── create_cost_center.py
│   └── set_budget_target.py
└── queries/
    ├── __init__.py
    └── get_hierarchy_budget.py
```

Callers (routers, dependencies, and test files) import directly from the new canonical packages (`src.budgeting.application.commands` and `src.budgeting.application.queries`). No shim files or intermediate `use_cases/` directories are retained.

Same structure for:

- `src/allocation/application/`:
  - `commands/`: `register_accounting_account.py`, `register_contract.py`, `submit_measurement.py`, `approve_measurement.py`
  - `queries/`: `list_accounting_accounts.py`, `list_contracts.py`, `list_measurements.py`, `get_cost_center_accounting_breakdown.py`
- `src/indicators/application/`:
  - `commands/`: *(none - indicators is a query/simulation context)*
  - `queries/`: `compute_period_indicators.py`, `material_impact.py`, `simulate_scenario.py`
- `src/intelligence/application/`:
  - `commands/`: *(none - caching is handled inside orchestration)*
  - `queries/`: `analyze_allocation_anomalies.py`, `generate_executive_summary.py`

### 5.2 Allocation Models and DTOs Modularization

Convert `src/allocation/infrastructure/database/models.py` into a package:

```text
src/allocation/infrastructure/database/models/
├── __init__.py             # Exports SupplierModel, ContractModel, MeasurementModel, etc.
├── supplier.py
├── contract.py
├── measurement.py
└── accounting_account.py
```

*Note on Alembic Discovery:* `models/__init__.py` explicitly imports all model submodules, ensuring that `migrations/env.py` and SQLAlchemy's `Base.metadata` automatically discover and register all tables identically with zero schema drift.

Convert `src/allocation/application/dto.py` into a package:

```text
src/allocation/application/dto/
├── __init__.py             # Exports all DTOs
├── supplier.py
├── contract.py
├── measurement.py
└── accounting.py
```

### 5.3 Presentation Routers

Split `src/presentation/api/v1/allocation_router.py` into:

- `src/presentation/api/v1/contracts_router.py`: Contract registration and querying.
- `src/presentation/api/v1/measurements_router.py`: Measurement submission, approval, and listing.
- Keep `accounting_router.py` for accounting accounts and breakdown endpoints.
- Update `src/presentation/api/v1/__init__.py` and `app.py` to mount the specific routers directly under `/api/v1/`.

### 5.4 Modular Composition Root (`src/presentation/dependencies/`)

Decompose `src/presentation/dependencies.py` (771 lines) into:

```text
src/presentation/dependencies/
├── __init__.py             # Exposes get_container, set_container, reset_container, DependencyContainer
├── container.py            # DependencyContainer facade coordinating context modules
├── budgeting.py            # Budgeting repositories, session wrappers, and use cases
├── allocation.py           # Allocation repositories, session wrappers, and use cases
├── indicators.py           # Indicators services and use cases
├── intelligence.py         # Intelligence repositories, AI ports, and use cases
└── database.py             # Database engine, session factory, and initialization lifecycle
```

*Note on Facade Design:* The `DependencyContainer` facade preserves all public property names (`container.create_cost_center_use_case`, `container.allocation_repository`, `container.ai_port`, etc.) by delegating to the context providers, allowing clean dependency injection and seamless test double injection.

### 5.5 Co-Location of Session-Managed Repositories

Move `SessionManaged*Repository` classes from `src/shared/infrastructure/database/repositories.py` directly into each context's infrastructure repository folder:

- `src/budgeting/infrastructure/repositories/session_managed.py`
- `src/allocation/infrastructure/repositories/session_managed.py`
- `src/intelligence/infrastructure/repositories/session_managed.py`
- Delete `src/shared/infrastructure/database/repositories.py` once dependencies point to the context-specific modules.

### 5.6 Modular Seeding Script (`scripts/`)

Decompose `scripts/seed_ai_data.py` (639 lines) into:

```text
scripts/
├── seed/
│   ├── __init__.py
│   ├── data.py             # Synthetic enterprise data definitions (cost centers, budgets, contracts, rateios)
│   ├── seeder.py           # Database transaction execution steps
│   └── runner.py           # Verification, anomaly checking, and executive AI summary execution
└── seed_ai_data.py         # Thin CLI entry point importing and executing the runner
```

---

## 6. What's Left to the Builder

- Creating directories and files with proper `__all__` and relative imports.
- Running `pytest` after each module refactoring step to verify zero regressions.
- Running `ruff check .`, `ruff format .`, and `pyrefly check` to ensure strict code quality and formatting.
- Committing each logical refactoring phase cleanly with Gitmoji and Conventional Commits.

# Design Specification: Architectural Refinements (Clean Architecture, DDD, Hexagonal & CQRS)

**Date:** 2026-11-13  
**Status:** In Review / Ready for Builder Check  
**Author:** Antigravity  
**Branch:** `feature/architecture-refinements` (forked from `develop`)  
**Source Review:** [`docs/clean-ddd-hexagonal-architecture-review.md`](../clean-ddd-hexagonal-architecture-review.md)

---

## 1. Intent & Context

Following the comprehensive Clean Architecture, DDD, and Hexagonal Architecture review ([`docs/clean-ddd-hexagonal-architecture-review.md`](../clean-ddd-hexagonal-architecture-review.md)), four actionable architectural refinements were identified. While the codebase achieved 100% test coverage and strict layer isolation, addressing these four areas eliminates minor symmetry and placement inconsistencies across bounded contexts, API routing, test suites, and CQRS documentation.

The goal is to implement these refinements cleanly in a single cohesive feature branch without disrupting existing behavior, breaking contracts, or compromising domain boundaries.

---

## 2. Goals, Non-Goals & Anti-Goals

### 2.1 Goals
- **G1 (Port Placement Consistency):** Relocate `AIAnalysisCacheRepository` from `src/intelligence/application/ports/` to `src/intelligence/domain/repositories/`, achieving tactical DDD uniformity with `allocation` and `budgeting` (where entity repository protocols live in the domain layer).
- **G2 (Router-to-Test Symmetry):** Extract the `POST /scenarios/simulate` endpoint from `src/presentation/api/v1/indicators_router.py` into a dedicated `src/presentation/api/v1/scenarios_router.py`, achieving 1:1 symmetry with `tests/api/test_scenarios_api.py`.
- **G3 (API Test File Uniformity):** Standardize all test file names under `tests/api/` to follow the `test_<resource>_api.py` convention (renaming `test_api_accounting.py` and `test_api_budgeting.py`).
- **G4 (CQRS Intent Documentation):** Add explicit module-level docstrings in `src/indicators/application/use_cases/__init__.py` and `src/intelligence/application/use_cases/__init__.py` documenting that these contexts operate strictly as read-only analytical projections.
- **G5 (Strict Verification):** Preserve 100% green status on all 171 tests, with zero Ruff and Pyrefly errors.

### 2.2 Non-Goals
- Introducing asynchronous Domain Events or an Outbox table at this time (reserved for future scalability roadmap).
- Modifying underlying calculation logic or domain algorithms (`ExactPennyAllocator`, `BudgetVarianceCalculator`, `AllocationAnomalyDetector`).
- Changing API response schemas or HTTP status codes.

### 2.3 Anti-Goals
- Retaining backwards-compatibility shims or duplicate re-exports (per user mandate, greenfield project rules apply).
- Re-exporting use case classes from `use_cases/__init__.py`.
- Leaking framework dependencies into domain layers.

---

## 3. Approaches Considered & Selected

### Approach 1: Sequential Atomic Slicing (Selected)
- Implements each of the 4 refinements as an independent, atomic commit with Conventional Commits + Gitmoji.
- Verifies the full test suite (`pytest`), linter (`ruff`), and type checker (`pyrefly`) after each commit.
- **Trade-off:** Slightly more git operations, but provides pristine auditability, zero broken intermediate states, and immediate pinpointing of any regression.

### Approach 2: Monolithic Single-Commit Refactoring (Rejected)
- Applies all file moves, router extractions, and test renames in one large commit.
- **Trade-off:** Conflates presentation, domain, and test layers into a single diff, obscuring review and violating `AGENTS.md` commit standards.

### Approach 3: Independent Micro-Branches per Item (Rejected)
- Opens four separate git branches and pull requests.
- **Trade-off:** High workflow overhead for tightly related, non-conflicting improvements already approved as a single package.

---

## 4. Detailed Design: The Four Refinements

### 4.1 Refinement 1: Relocate `AIAnalysisCacheRepository` to Domain Layer

#### Context & Rationale
In `src/intelligence/domain/cache.py`, `AIAnalysisCache` is a rich domain entity encapsulating cache lifecycle, drift evaluation, and renewal logic. In the `allocation` and `budgeting` bounded contexts, entity repository interfaces are placed in `domain/repositories/` (e.g., `src/allocation/domain/repositories/contract_repository.py`). Placing `AIAnalysisCacheRepository` in `application/ports/` created an asymmetry.

#### Execution Plan:
1. Create `src/intelligence/domain/repositories/` directory.
2. Move `src/intelligence/application/ports/ai_analysis_cache_repository.py` to `src/intelligence/domain/repositories/ai_analysis_cache_repository.py`.
3. Create `src/intelligence/domain/repositories/__init__.py`:
   ```python
   """Intelligence domain repository interfaces."""

   from .ai_analysis_cache_repository import AIAnalysisCacheRepository

   __all__ = ["AIAnalysisCacheRepository"]
   ```
4. Update imports across:
   - `src/intelligence/application/use_cases/queries/generate_executive_summary.py`
   - `src/intelligence/infrastructure/repositories/in_memory_ai_cache_repository.py`
   - `src/intelligence/infrastructure/repositories/sqlalchemy_ai_cache_repository.py`
   - `src/intelligence/infrastructure/repositories/session_managed.py`
   - `src/presentation/dependencies/intelligence.py`
   - `src/presentation/dependencies/container.py`
   - `tests/unit/intelligence/application/use_cases/queries/test_executive_summary_caching.py`
   - `tests/unit/intelligence/application/use_cases/queries/test_analyze_allocation_anomalies.py`
5. Note on `AIPort`: `AIPort` remains in `src/intelligence/application/ports/ai_port.py` because it is an outbound application service port connecting to an external AI provider (LLM), not an aggregate entity persistence contract.

---

### 4.2 Refinement 2: Extract `scenarios_router.py` from `indicators_router.py`

#### Context & Rationale
Currently, `POST /scenarios/simulate` is hosted within `src/presentation/api/v1/indicators_router.py`. However, during the CQRS modularization, integration tests were cleanly extracted into `tests/api/test_scenarios_api.py`. Extracting a dedicated router aligns with 1:1 file symmetry and single-responsibility routing.

#### Execution Plan:
1. Create `src/presentation/api/v1/scenarios_router.py`:
   - Prefix: `/api/v1`
   - Tags: `["What-If Scenarios"]`
   - Dependency: `SimulateScenarioUseCaseDep`
   - Endpoint: `POST /scenarios/simulate` returning `ScenarioSimulationResponse`
   - Docstrings and OpenAPI summary preserved.
2. In `src/presentation/api/v1/indicators_router.py`:
   - Remove the `/scenarios/simulate` route and its unused dependencies/schemas (`SimulateScenarioUseCaseDep`, `ScenarioSimulationRequest`, `ScenarioSimulationResponse`, `ScenarioImpactResponse`).
3. Update `src/presentation/api/v1/__init__.py`:
   - Export `scenarios_router`.
4. In `src/presentation/app.py`:
   - Include `scenarios_router`:
     ```python
     app.include_router(scenarios_router)
     ```
5. Verify `tests/api/test_scenarios_api.py` passes against the extracted router without modifying any test logic.

---

### 4.3 Refinement 3: Standardize API Test Naming to `test_*_api.py`

#### Context & Rationale
Within `tests/api/`, the test suite previously mixed two naming styles:
- `test_api_accounting.py`
- `test_api_budgeting.py`
vs.
- `test_contracts_api.py`
- `test_measurements_api.py`
- `test_indicators_api.py`
- `test_intelligence_api.py`
- `test_scenarios_api.py`

#### Execution Plan:
1. `git mv tests/api/test_api_accounting.py tests/api/test_accounting_api.py`
2. `git mv tests/api/test_api_budgeting.py tests/api/test_budgeting_api.py`
3. Resulting `tests/api/` layout:
   ```text
   tests/api/
   ├── conftest.py
   ├── test_accounting_api.py
   ├── test_budgeting_api.py
   ├── test_contracts_api.py
   ├── test_indicators_api.py
   ├── test_intelligence_api.py
   ├── test_measurements_api.py
   └── test_scenarios_api.py
   ```

---

### 4.4 Refinement 4: Document Read-Only CQRS Analytical Projections

#### Context & Rationale
In CQRS, bounded contexts that only perform analysis, calculation, and reporting do not expose commands (mutations). To prevent confusion for developers or AI agents expecting a `commands/` directory, explicit module-level docstrings must document this design choice.

#### Execution Plan:
1. Update `src/indicators/application/use_cases/__init__.py`:
   ```python
   """Indicators application use cases package.

   Architecture Note (CQRS):
   The Strategic Indicators bounded context operates strictly as a read-only
   analytical projection. It consumes data from upstream operational contexts
   (Allocation and Budgeting) to compute deterministic variance metrics,
   materiality rankings, and What-If simulations. As such, it contains only
   queries under the queries/ subpackage, with no mutation commands.
   """
   ```
2. Update `src/intelligence/application/use_cases/__init__.py`:
   ```python
   """Intelligence application use cases package.

   Architecture Note (CQRS):
   The Strategic Intelligence bounded context operates as a cognitive and
   analytical projection layer. It synthesizes indicators and historical
   allocations to detect anomalies and generate AI executive summaries.
   All use cases in this context are organized as queries under the queries/
   subpackage, with no mutation commands.
   """
   ```

---

## 5. Verification & Quality Gates

Each task and the final branch must pass all quality gates specified in `AGENTS.md`:

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
```

- **Zero regressions:** 171 passed tests.
- **Zero linter warnings:** Ruff clean.
- **Zero type errors:** Pyrefly strict type compliance.
- **Zero dead code:** No obsolete files or shims retained.

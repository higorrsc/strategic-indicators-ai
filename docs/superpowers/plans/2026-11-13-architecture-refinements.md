# Architectural Refinements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the four targeted architectural refinements identified in the Clean Architecture, DDD, and Hexagonal review: relocate the AI cache repository protocol to the domain layer, extract a dedicated What-If scenarios router, standardize API test filenames, and document read-only CQRS projections.

**Architecture:** Maintain strict Clean Architecture inward dependencies and DDD tactical symmetry. Entity repository interfaces belong in `domain/repositories/` of their respective bounded context, while external service integrations (like LLMs) remain in `application/ports/`. Presentation routers achieve 1:1 file symmetry with their API test suites, and CQRS intent is clearly documented in package docstrings.

**Tech Stack:** Python 3.15, FastAPI, SQLAlchemy (asyncio), Pydantic v2, Pytest, Ruff, Pyrefly.

**Spec:** [`docs/superpowers/specs/2026-11-13-architecture-refinements-design.md`](../specs/2026-11-13-architecture-refinements-design.md)

## Global Constraints
- Target branch: `feature/architecture-refinements` (forked from `develop`).
- Conventional Commits with Gitmoji mandatory for every commit.
- Domain layer must remain 100% free of framework imports (`fastapi`, `sqlalchemy`, `pydantic`, etc.).
- Zero backwards-compatibility shims or duplicate re-exports retained.
- Quality gates: `uv run pytest` (171 passed), `uv run ruff check .` (0 errors), `uv run pyrefly check` (0 errors).

## Review Focus
- In `src/intelligence/domain/repositories/ai_analysis_cache_repository.py`, verify `AIAnalysisCacheRepository` remains a pure `typing.Protocol` without external I/O or framework imports.
- In `src/presentation/api/v1/scenarios_router.py`, verify the route path remains exactly `/api/v1/scenarios/simulate` with `tags=["What-If Scenarios"]` so client contracts and existing API tests remain intact.
- In `src/presentation/api/v1/indicators_router.py`, verify that extracting scenarios does not leave behind unused imports (`ScenarioSimulateRequest`, `SimulationResultResponse`, `CostCenterImpactResponse`, `SimulateScenarioUseCaseDep`).
- In `tests/api/`, verify that `test_accounting_api.py` and `test_budgeting_api.py` execute identically under their new names with no missing fixtures.

---

### Task 1: Relocate `AIAnalysisCacheRepository` Port to Domain Layer

**Files:**
- Create: `src/intelligence/domain/repositories/ai_analysis_cache_repository.py`
- Create: `src/intelligence/domain/repositories/__init__.py`
- Delete: `src/intelligence/application/ports/ai_analysis_cache_repository.py`
- Modify: `src/intelligence/application/use_cases/queries/generate_executive_summary.py:15-18`
- Modify: `src/intelligence/infrastructure/repositories/in_memory_ai_cache_repository.py:6-9`
- Modify: `src/intelligence/infrastructure/repositories/sqlalchemy_ai_cache_repository.py:10-13`
- Modify: `src/intelligence/infrastructure/repositories/session_managed.py:7-10`
- Modify: `src/presentation/dependencies/intelligence.py:16-19`
- Modify: `src/presentation/dependencies/container.py:39-42`
- Modify: `tests/unit/intelligence/application/use_cases/queries/test_executive_summary_caching.py:35-40`
- Modify: `tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py:9-14`
- Modify: `README.md` (architecture tree reference)

**Interfaces:**
- Consumes: `src.intelligence.domain.cache.AIAnalysisCache`
- Produces: `src.intelligence.domain.repositories.AIAnalysisCacheRepository` with methods:
  ```python
  class AIAnalysisCacheRepository(Protocol):
      async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None: ...
      async def save(self, cache: AIAnalysisCache) -> None: ...
      async def delete_by_key(self, cache_key: str) -> None: ...
  ```

- [ ] **Step 1: Create `src/intelligence/domain/repositories/ai_analysis_cache_repository.py`**
  Move the protocol from `src/intelligence/application/ports/ai_analysis_cache_repository.py` to `src/intelligence/domain/repositories/ai_analysis_cache_repository.py`:
  ```python
  """Repository port for AI analysis cache persistence."""

  from __future__ import annotations

  from typing import Protocol

  from src.intelligence.domain.cache import AIAnalysisCache


  class AIAnalysisCacheRepository(Protocol):
      """Interface defining persistence operations for AI analysis cache entries."""

      async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None:
          """Retrieve cached analysis by unique cache key."""
          ...

      async def save(self, cache: AIAnalysisCache) -> None:
          """Persist or update an AI analysis cache entry."""
          ...

      async def delete_by_key(self, cache_key: str) -> None:
          """Remove a cached analysis by key."""
          ...
  ```

- [ ] **Step 2: Create `src/intelligence/domain/repositories/__init__.py`**
  ```python
  """Intelligence domain repositories package."""

  from .ai_analysis_cache_repository import AIAnalysisCacheRepository

  __all__ = ["AIAnalysisCacheRepository"]
  ```

- [ ] **Step 3: Delete old `src/intelligence/application/ports/ai_analysis_cache_repository.py`**
  Remove the obsolete file. In `src/intelligence/application/ports/__init__.py`, verify only `AIPort`, `ExecutiveSummaryResponse`, and `ScenarioEvaluationResponse` are exported.

- [ ] **Step 4: Update imports across application, infrastructure, presentation, and tests**
  Change all occurrences of `from src.intelligence.application.ports.ai_analysis_cache_repository import AIAnalysisCacheRepository` (or `from src.intelligence.application.ports import AIAnalysisCacheRepository`) to:
  `from src.intelligence.domain.repositories import AIAnalysisCacheRepository` (or `from src.intelligence.domain.repositories.ai_analysis_cache_repository import AIAnalysisCacheRepository`).
  Files to update:
  - `src/intelligence/application/use_cases/queries/generate_executive_summary.py`
  - `src/intelligence/infrastructure/repositories/in_memory_ai_cache_repository.py`
  - `src/intelligence/infrastructure/repositories/sqlalchemy_ai_cache_repository.py`
  - `src/intelligence/infrastructure/repositories/session_managed.py`
  - `src/presentation/dependencies/intelligence.py`
  - `src/presentation/dependencies/container.py`
  - `tests/unit/intelligence/application/use_cases/queries/test_executive_summary_caching.py`
  - `tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py`
  - `README.md` (line 120)

- [ ] **Step 5: Run tests and verify**
  Run: `uv run pytest tests/unit/intelligence/ tests/integration/intelligence/ && uv run ruff check . && uv run pyrefly check`
  Expected: All intelligence unit and integration tests PASS with 0 lint/typing errors.

- [ ] **Step 6: Commit**
  ```bash
  git add src/intelligence/domain/repositories/ src/intelligence/application/ports/ src/intelligence/infrastructure/ src/presentation/dependencies/ tests/unit/intelligence/ tests/integration/intelligence/ README.md
  git commit -m "♻️ refactor(intelligence): relocate ai analysis cache repository port to domain layer"
  ```

---

### Task 2: Extract `scenarios_router.py` from `indicators_router.py`

**Files:**
- Create: `src/presentation/api/v1/scenarios_router.py`
- Modify: `src/presentation/api/v1/indicators_router.py:15-30,90-160`
- Modify: `src/presentation/api/v1/__init__.py:1-18`
- Modify: `src/presentation/app.py:10-20,60-70`

**Interfaces:**
- Consumes: `src.presentation.dependencies.SimulateScenarioUseCaseDep`, `src.presentation.schemas.indicators.ScenarioSimulateRequest`, `src.presentation.schemas.indicators.SimulationResultResponse`, `src.presentation.schemas.indicators.CostCenterImpactResponse`
- Produces: `src.presentation.api.v1.scenarios_router.router` handling `POST /api/v1/scenarios/simulate`

- [ ] **Step 1: Create `src/presentation/api/v1/scenarios_router.py`**
  ```python
  """FastAPI router for What-If scenario simulation endpoints."""

  from __future__ import annotations

  from decimal import Decimal
  from uuid import UUID

  from fastapi import APIRouter

  from src.indicators.application.dto import (
      AllocationShiftDTO,
      SimulateScenarioCommand,
  )
  from src.presentation.dependencies import SimulateScenarioUseCaseDep
  from src.presentation.schemas.indicators import (
      CostCenterImpactResponse,
      ScenarioSimulateRequest,
      SimulationResultResponse,
  )

  router = APIRouter(prefix="/api/v1", tags=["What-If Scenarios"])


  @router.post(
      "/scenarios/simulate",
      response_model=SimulationResultResponse,
      summary="Execute in-memory what-if scenario simulation",
  )
  async def simulate_scenario(
      request: ScenarioSimulateRequest,
      use_case: SimulateScenarioUseCaseDep,
  ) -> SimulationResultResponse:
      """Evaluate contract inflation and allocation shifts in memory.

      Args:
          request: Simulation parameters payload.
          use_case: SimulateScenarioUseCase dependency.

      Returns:
          SimulationResultResponse: Comparative differential simulation report.
      """
      contract_adjustments: dict[UUID, Decimal] = {
          UUID(k): v for k, v in request.contract_inflation.items()
      }

      shifts = [
          AllocationShiftDTO(
              from_cost_center_id=s.from_cost_center_id,
              to_cost_center_id=s.to_cost_center_id,
              percentage_points=s.percentage_points,
              contract_id=s.contract_id,
          )
          for s in request.allocation_shifts
      ]

      command = SimulateScenarioCommand(
          scenario_name=request.name,
          period=request.period,
          contract_cost_adjustments=contract_adjustments,
          allocation_shifts=shifts,
      )
      result = await use_case.execute(command)

      total_baseline = sum(
          (imp.baseline_actual for imp in result.impacts), Decimal("0.00")
      )
      total_simulated = sum(
          (imp.simulated_actual for imp in result.impacts), Decimal("0.00")
      )
      total_delta = sum((imp.delta_actual for imp in result.impacts), Decimal("0.00"))
      overruns_count = sum(1 for imp in result.impacts if imp.new_overrun)

      return SimulationResultResponse(
          scenario_name=result.scenario_name,
          period=result.period,
          impacts=[
              CostCenterImpactResponse(
                  cost_center_id=imp.cost_center_id,
                  cost_center_code=imp.cost_center_code,
                  baseline_actual=imp.baseline_actual,
                  simulated_actual=imp.simulated_actual,
                  delta_actual=imp.delta_actual,
                  baseline_status=imp.baseline_status,
                  simulated_status=imp.simulated_status,
                  new_overrun=imp.new_overrun,
              )
              for imp in result.impacts
          ],
          new_overruns_count=overruns_count,
          total_baseline_actual=total_baseline,
          total_simulated_actual=total_simulated,
          total_delta=total_delta,
      )
  ```

- [ ] **Step 2: Remove `/scenarios/simulate` from `indicators_router.py`**
  In `src/presentation/api/v1/indicators_router.py`:
  - Change router tag from `tags=["Budget Indicators & Simulations"]` to `tags=["Budget Indicators"]`.
  - Remove `AllocationShiftDTO` and `SimulateScenarioCommand` from `src.indicators.application.dto` imports.
  - Remove `SimulateScenarioUseCaseDep` from `src.presentation.dependencies` imports.
  - Remove `CostCenterImpactResponse`, `ScenarioSimulateRequest`, `SimulationResultResponse` from `src.presentation.schemas.indicators` imports.
  - Delete `simulate_scenario` endpoint function entirely.

- [ ] **Step 3: Register `scenarios_router` in `src/presentation/api/v1/__init__.py` and `app.py`**
  - In `src/presentation/api/v1/__init__.py`:
    ```python
    from .scenarios_router import router as scenarios_router

    __all__ = [
        "accounting_router",
        "budgeting_router",
        "contracts_router",
        "indicators_router",
        "intelligence_router",
        "measurements_router",
        "scenarios_router",
    ]
    ```
  - In `src/presentation/app.py`:
    Import `scenarios_router` and add `app.include_router(scenarios_router)`.

- [ ] **Step 4: Run tests and verify**
  Run: `uv run pytest tests/api/test_scenarios_api.py tests/api/test_indicators_api.py && uv run ruff check . && uv run pyrefly check`
  Expected: Both API tests PASS with 0 errors.

- [ ] **Step 5: Commit**
  ```bash
  git add src/presentation/api/v1/scenarios_router.py src/presentation/api/v1/indicators_router.py src/presentation/api/v1/__init__.py src/presentation/app.py
  git commit -m "♻️ refactor(api): extract scenarios router from indicators router"
  ```

---

### Task 3: Standardize API Test Naming to `test_*_api.py`

**Files:**
- Move: `tests/api/test_api_accounting.py` -> `tests/api/test_accounting_api.py`
- Move: `tests/api/test_api_budgeting.py` -> `tests/api/test_budgeting_api.py`

**Interfaces:**
- Consumes: Existing pytest test functions in both files.
- Produces: Uniform test discovery under `tests/api/test_*_api.py`.

- [ ] **Step 1: Move test files using `git mv`**
  ```bash
  git mv tests/api/test_api_accounting.py tests/api/test_accounting_api.py
  git mv tests/api/test_api_budgeting.py tests/api/test_budgeting_api.py
  ```

- [ ] **Step 2: Run pytest across the entire `tests/api/` directory**
  Run: `uv run pytest tests/api/`
  Expected: All 26 API tests pass in `test_accounting_api.py`, `test_budgeting_api.py`, `test_contracts_api.py`, `test_indicators_api.py`, `test_intelligence_api.py`, `test_measurements_api.py`, and `test_scenarios_api.py`.

- [ ] **Step 3: Run linters and type check**
  Run: `uv run ruff check . && uv run pyrefly check`
  Expected: 0 errors.

- [ ] **Step 4: Commit**
  ```bash
  git commit -m "♻️ refactor(tests): standardize api test filenames to test_*_api pattern"
  ```

---

### Task 4: Document Read-Only CQRS Analytical Projections

**Files:**
- Modify: `src/indicators/application/use_cases/__init__.py`
- Modify: `src/intelligence/application/use_cases/__init__.py`

**Interfaces:**
- Consumes: Existing package structures in `indicators` and `intelligence`.
- Produces: Clear architectural docstrings explaining why no `commands/` directory exists in these two bounded contexts.

- [ ] **Step 1: Update `src/indicators/application/use_cases/__init__.py`**
  Add the architectural rationale:
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

- [ ] **Step 2: Update `src/intelligence/application/use_cases/__init__.py`**
  Add the architectural rationale:
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

- [ ] **Step 3: Run full verification suite**
  Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
  Expected: 171 passed tests, 0 lint errors, 0 type errors.

- [ ] **Step 4: Commit**
  ```bash
  git add src/indicators/application/use_cases/__init__.py src/intelligence/application/use_cases/__init__.py
  git commit -m "📝 docs(cqrs): document read-only analytical projections in use cases packages"
  ```

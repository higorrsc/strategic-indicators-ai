# Tasks: Strategic Budget Indicators System

## 1. Project Dependencies & Shared Domain Foundation

- [x] 1.1 Ingest core project dependencies (`fastapi`, `pydantic>=2.0`, `pydantic-settings`, `pydantic-ai`, `pytest-bdd`, `httpx`) in `pyproject.toml` and verify with `uv sync`
- [x] 1.2 Implement shared Value Objects (`Money`, `Percentage`, `Period`, `CostCenterCode`) in `src/shared/domain/value_objects/` and verify with unit tests in `tests/unit/shared/`
- [x] 1.3 Create centralized application configuration with `pydantic-settings` in `src/shared/config/settings.py` supporting `AI_PROVIDER`, `AI_MODEL`, and `AI_BASE_URL`

## 2. Budgeting Bounded Context

- [x] 2.1 Implement `CostCenter` aggregate entity with hierarchical tree links and cycle detection in `src/budgeting/domain/entities/cost_center.py` and verify with unit tests
- [x] 2.2 Implement `BudgetTarget` entity in `src/budgeting/domain/entities/budget_target.py` with non-negative monetary target invariants and verify with unit tests
- [x] 2.3 Implement repository interface and in-memory test double for cost centers and budgets in `src/budgeting/domain/repositories/`
- [x] 2.4 Implement application use cases (`CreateCostCenterUseCase`, `SetBudgetTargetUseCase`, `GetHierarchyBudgetUseCase`) in `src/budgeting/application/use_cases/` and verify with application unit tests

## 3. Cost Allocation Bounded Context

- [x] 3.1 Implement `Supplier` and `Contract` entities with default allocation templates in `src/allocation/domain/entities/` and verify with unit tests
- [x] 3.2 Implement `Measurement` aggregate entity with lifecycle states (`DRAFT`, `SUBMITTED`, `APPROVED`, `CANCELLED`) and immutable state transition guards in `src/allocation/domain/entities/measurement.py`
- [x] 3.3 Implement `ExactPennyAllocator` domain service reconciling rounding discrepancies and validating 100% distribution in `src/allocation/domain/services/allocator.py` and verify with unit tests
- [x] 3.4 Implement repository interfaces and in-memory test doubles in `src/allocation/domain/repositories/`
- [x] 3.5 Implement use cases (`RegisterContractUseCase`, `SubmitMeasurementUseCase`, `ApproveMeasurementUseCase`) in `src/allocation/application/use_cases/` and verify with application unit tests

## 4. Budget Indicators & Simulation Bounded Context

- [x] 4.1 Implement `BudgetVarianceCalculator` domain service computing variance, execution rate, and threshold alerts (`NORMAL`, `WARNING`, `CRITICAL_OVERRUN`) in `src/indicators/domain/services/variance_calculator.py` and verify with unit tests
- [x] 4.2 Implement `WhatIfSimulator` domain service evaluating cost inflation adjustments and allocation shifts in-memory in `src/indicators/domain/services/simulator.py` and verify with unit tests
- [x] 4.3 Implement use cases (`ComputePeriodIndicatorsUseCase`, `SimulateScenarioUseCase`) in `src/indicators/application/use_cases/` and verify with application unit tests

## 5. Strategic Intelligence Context (Multi-Provider AI & Anomaly Detection)

- [x] 5.1 Implement `AllocationAnomalyDetector` domain service with abrupt shift and budget dumping heuristics in `src/intelligence/domain/services/anomaly_detector.py` and verify with unit tests
- [x] 5.2 Define `AIPort` protocol with typed schemas (`ExecutiveSummaryResponse`, `ScenarioEvaluationResponse`) in `src/intelligence/application/ports/ai_port.py`
- [x] 5.3 Implement `FakeAIPort` for deterministic local testing in `src/intelligence/infrastructure/fake_ai_adapter.py` and verify with test suite
- [x] 5.4 Implement `PydanticAIAdapter` supporting local Ollama (`http://localhost:11434/v1`), Google Gemini, and OpenAI backends in `src/intelligence/infrastructure/pydantic_ai_adapter.py`
- [x] 5.5 Implement use cases (`GenerateExecutiveSummaryUseCase`, `AnalyzeAllocationAnomaliesUseCase`) in `src/intelligence/application/use_cases/` and verify with unit tests

## 6. Presentation Layer & OpenAPI Contracts

- [x] 6.1 Implement FastAPI presentation router and Pydantic DTOs for `budgeting` endpoints (`/api/v1/cost-centers`, `/api/v1/budgets`) and verify with HTTP test client
- [x] 6.2 Implement FastAPI presentation router and Pydantic DTOs for `allocation` endpoints (`/api/v1/contracts`, `/api/v1/measurements`) and verify with HTTP test client
- [x] 6.3 Implement FastAPI presentation router and Pydantic DTOs for `indicators` and `intelligence` endpoints (`/api/v1/indicators/{period}`, `/api/v1/scenarios/simulate`, `/api/v1/intelligence/executive-summary`) and verify with HTTP test client
- [x] 6.4 Write BDD feature specifications and step definitions with `pytest-bdd` verifying end-to-end acceptance scenarios across all capabilities in `tests/bdd/`

## 7. Quality Assurance & Static Verification

- [x] 7.1 Run code formatter (`uv run ruff format .`) and verify style compliance
- [x] 7.2 Run linter (`uv run ruff check .`) and resolve all warnings
- [x] 7.3 Run static type checker (`uv run pyrefly check`) and confirm zero type errors
- [x] 7.4 Execute complete test suite (`uv run pytest`) and confirm all unit, integration, and BDD tests pass

## Workflow follow-up

- Archive the change after the project's review requirements are satisfied.
- Verify the archived specifications in `openspec/specs/`.

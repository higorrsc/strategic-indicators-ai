# Tasks: Material Impact & Effort Prioritization Analysis

- [x] 1. Domain Modeling & Calculation Engine
  - [x] 1.1 Define enums `AggregationLevel` (`cost_center`, `hierarchy`, `accounting_account`), `FocusMetric`, and `ActionPriority` in `src/domain/indicators/types.py`
  - [x] 1.2 Implement `MaterialityAnalyzer` domain service in `src/domain/indicators/services/materiality_analyzer.py`
  - [x] 1.3 Write pure domain unit tests for `MaterialityAnalyzer` in `tests/unit/indicators/test_materiality_analyzer.py` covering:
    - Normal spend Pareto ranking (80/15/5 distribution)
    - Overrun variance ranking
    - Zero-variance handling
    - Single-entity vs multi-entity scenarios
    - Accounting account aggregation calculations


- [x] 2. Application Use Cases & DTOs
  - [x] 2.1 Define `MaterialityItemDTO` and `MaterialImpactReportDTO` in `src/application/dto/indicators.py`
  - [x] 2.2 Implement `GenerateMaterialImpactReportUseCase` in `src/application/use_cases/indicators/material_impact.py`
  - [x] 2.3 Implement hierarchical rollup logic grouping children by root parent cost center
  - [x] 2.4 Implement accounting account aggregation logic (both global and scoped by `cost_center_id`)
  - [x] 2.5 Write application use case unit tests in `tests/unit/indicators/test_material_impact_use_case.py`


- [x] 3. Presentation & API Layer
  - [x] 3.1 Define Pydantic response models in `src/presentation/schemas/materiality.py`
  - [x] 3.2 Add endpoint `GET /api/v1/indicators/{period}/materiality-focus` in `src/presentation/api/v1/indicators_router.py` supporting `level=accounting_account` and optional `cost_center_id`
  - [x] 3.3 Register dependencies in `src/presentation/dependencies.py`
  - [x] 3.4 Write API integration tests in `tests/api/test_api_indicators_and_intelligence.py` verifying query combinations:
    - `level=cost_center&metric=variance`
    - `level=hierarchy&metric=spend`
    - `level=accounting_account&metric=spend`
    - `level=accounting_account&cost_center_id=<uuid>&metric=variance`
    - `threshold_pct=80`


- [ ] 4. Documentation & Verification
  - [ ] 4.1 Run full quality suite (`uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`)
  - [ ] 4.2 Update `README.md` and OpenAPI documentation

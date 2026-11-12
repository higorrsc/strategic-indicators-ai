# Tasks: List Contracts and Measurements Endpoints

## 1. Domain & Repository Enhancements

- [x] 1.1 Extend `MeasurementRepository` protocol with multi-criteria `find(period, contract_id, state)` and verify interface conformance via type checker (`uv run pyrefly check`)
- [x] 1.2 Implement `find` in `InMemoryMeasurementRepository` and verify with unit tests in `tests/unit/allocation/test_allocation.py`
- [x] 1.3 Implement `find` in `SqlAlchemyMeasurementRepository` and `SessionManagedMeasurementRepository` and verify with database integration tests in `tests/integration/database/test_allocation_persistence.py`

## 2. Application Layer Use Cases

- [x] 2.1 Implement `ListContractsQuery` and `ListContractsUseCase` in `src/allocation/application/use_cases/list_contracts.py` and verify with unit tests
- [x] 2.2 Implement `ListMeasurementsQuery` and `ListMeasurementsUseCase` in `src/allocation/application/use_cases/list_measurements.py` and verify with unit tests
- [x] 2.3 Wire new use cases and dependencies into `DependencyContainer` in `src/presentation/dependencies.py`

## 3. Presentation Layer Endpoints & Verification

- [x] 3.1 Expose `GET /api/v1/contracts` in `src/presentation/api/v1/allocation_router.py` with `active_only` and `supplier_id` query parameters
- [x] 3.2 Expose `GET /api/v1/measurements` in `src/presentation/api/v1/allocation_router.py` with `period`, `contract_id`, and `state` query parameters
- [x] 3.3 Add API tests in `tests/api/test_api_allocation.py` verifying contract and measurement collection endpoints and verify with `uv run pytest tests/api/test_api_allocation.py`
- [x] 3.4 Run full regression test suite, linting, formatting, and type checks (`uv run ruff check .`, `uv run ruff format --check .`, `uv run pyrefly check`, `uv run pytest`)

# Proposal: List Contracts and Measurements Endpoints

## Why

Currently, the Cost Allocation API supports contract registration (`POST /api/v1/contracts`), single contract lookup by ID (`GET /api/v1/contracts/{contract_id}`), measurement submission (`POST /api/v1/measurements`), measurement approval (`POST /api/v1/measurements/{id}/approve`), and single measurement lookup (`GET /api/v1/measurements/{id}`).

However, consumers (such as frontend dashboards, Swagger UI testers, and automated audit scripts) cannot discover existing contracts or query historical measurements without already knowing their exact UUIDs. Providing list and query endpoints for contracts and measurements enables end-to-end operational visibility and simplifies downstream simulation and indicator testing.

## What Changes

- Add `GET /api/v1/contracts` endpoint to query contracts with optional filtering by `active_only` (default `true`) and `supplier_id`.
- Add `GET /api/v1/measurements` endpoint to query financial measurements with optional filtering by `period` (YYYY-MM), `contract_id`, and lifecycle `state` (`DRAFT`, `SUBMITTED`, `APPROVED`, `CANCELLED`).
- Introduce dedicated application use cases (`ListContractsUseCase` and `ListMeasurementsUseCase`) following Clean Architecture and DDD principles.
- Extend `MeasurementRepository` with multi-criteria query capability (`list_measurements(period, contract_id, state)`) across InMemory and SQLAlchemy session-managed implementations.

## Capabilities

### Modified Capabilities

- `cost-allocation`: Add requirements for listing contracts with supplier/active status filtering, and listing measurements with period/contract/state multi-criteria filtering.

## Impact

- **API & Presentation**:
  - `src/presentation/api/v1/allocation_router.py`: Add `GET /contracts` and `GET /measurements`.
  - `src/presentation/dependencies.py`: Wire `ListContractsUseCase` and `ListMeasurementsUseCase`.
- **Application Layer**:
  - `src/allocation/application/use_cases/list_contracts.py`: New use case and query DTO.
  - `src/allocation/application/use_cases/list_measurements.py`: New use case and query DTO.
- **Domain & Infrastructure Repositories**:
  - `src/allocation/domain/repositories/measurement_repository.py`: Add flexible filtering query method.
  - `src/allocation/infrastructure/repositories/`: Implement filtering query in `InMemoryMeasurementRepository` and `SqlAlchemyMeasurementRepository`.
  - `src/shared/infrastructure/database/repositories.py`: Update `SessionManagedMeasurementRepository`.
- **Tests**:
  - Unit tests for application use cases.
  - Integration tests for repository query methods.
  - API tests covering `GET /contracts` and `GET /measurements` with filters and pagination/defaults.

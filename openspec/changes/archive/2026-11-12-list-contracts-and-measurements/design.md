# Design: List Contracts and Measurements Endpoints

## Context

The Cost Allocation module models contracts, suppliers, measurements, and cost allocation entries with exact penny precision. Currently, data mutation operations (`POST /contracts`, `POST /measurements`, `POST /measurements/{id}/approve`) and singular lookups (`GET /contracts/{id}`, `GET /measurements/{id}`) are exposed. However, list and search capabilities are missing at the presentation layer despite underlying repository support (`ContractRepository.list_all` and `MeasurementRepository.list_by_period` / `list_by_contract`).

See `proposal.md` for user motivation and problem statement.

## Goals / Non-Goals

**Goals:**

- Expose RESTful collection endpoints `GET /api/v1/contracts` and `GET /api/v1/measurements` in `allocation_router`.
- Follow Clean Architecture: isolate query coordination inside application use cases (`ListContractsUseCase`, `ListMeasurementsUseCase`) and DTOs.
- Provide multi-criteria filtering for measurements (optional `period`, `contract_id`, and `state`) and contracts (optional `supplier_id`, `active_only`).
- Unify multi-criteria search in `MeasurementRepository` across in-memory and SQLAlchemy implementations.

**Non-Goals:**

- Pagination cursors / limit-offset overhead (current scale is enterprise accounting periods with tens to hundreds of measurements per month; simple filtered lists satisfy current domain requirements).
- Modifying measurement approval workflow or state transition rules.

## Decisions

### 1. Dedicated Application Use Cases vs. Direct Repository In Presentation

- **Decision**: Create `ListContractsUseCase` and `ListMeasurementsUseCase` in the application layer.
- **Rationale**: Preserves Clean Architecture boundaries (AGENTS.md Section 2 and 5). Route handlers delegate to use cases rather than calling repositories directly or orchestrating domain parsing logic.
- **Alternatives Considered**:
  - Direct repository calls in FastAPI routers: violates Clean Architecture layer inversion and couples presentation directly to repository protocols.

### 2. Multi-Criteria Query on `MeasurementRepository`

- **Decision**: Add `find(self, period: Period | None = None, contract_id: UUID | None = None, state: MeasurementState | None = None) -> list[Measurement]` to `MeasurementRepository`.
- **Rationale**: Consumers often want measurements for a specific contract in a given period (e.g. validating contract allocation trends) or all approved measurements in a period. A unified filter method avoids combinatorial repository methods (`list_by_period_and_contract_and_state`).
- **Alternatives Considered**:
  - Keep separate methods and filter in Python memory: degrades database query performance when thousands of historical records exist in PostgreSQL.

### 3. Query Parameter Validation in Presentation Layer

- **Decision**: Validate `period` format (`YYYY-MM`) and `state` enum values (`DRAFT`, `SUBMITTED`, `APPROVED`, `CANCELLED`) in FastAPI schemas/dependencies before converting to domain value objects (`Period`, `MeasurementState`).
- **Rationale**: FastAPI generates clear 422 validation errors if a client sends invalid formats, while the domain layer remains protected with strongly-typed value objects.

## Risks / Trade-offs

- **[Risk] Unfiltered Measurement Queries on Large Databases**: Querying `GET /api/v1/measurements` with no query parameters could return high volumes over multiple years.
  - *Mitigation*: In the presentation layer, encourage filtering by period. The database index on `measurements.period` ensures indexed performance.

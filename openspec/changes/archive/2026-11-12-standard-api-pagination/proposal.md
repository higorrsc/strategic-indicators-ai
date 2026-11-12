# Proposal: Standardized API Pagination

## Why

As enterprise financial data accumulates across multi-year fiscal periods, contracts, and measurement records, returning unbounded collections degrades database performance, increases payload transfer latency, and limits frontend usability. Introducing a standardized pagination envelope with pagination metadata and HATEOAS navigation links ensures bounded resource consumption, predictable response times, and consistent client pagination integration.

## What Changes

- **BREAKING**: Collection endpoints (`GET /api/v1/contracts`, `GET /api/v1/measurements`, and `GET /api/v1/cost-centers`) return a standardized paginated envelope `{ "data": [...], "pagination": {...}, "links": {...} }` instead of a bare JSON array.
- Standard query parameters on list endpoints: `page` (integer, default `1`, minimum `1`) and `perPage` (integer, default `20`, minimum `1`, maximum `100`).
- Consistent pagination metadata: `page`, `perPage`, `totalItems`, and `totalPages`.
- RFC-compliant HATEOAS navigation links: `self`, `first`, `last`, `next` (nullable), and `prev` (nullable), preserving any active filter query parameters.
- Reusable generic presentation models `PaginatedResponse[T]`, `PaginationMeta`, and `PaginationLinks`.
- Repository and use case support for efficient paginated queries and total count tracking.

## Capabilities

### New Capabilities

- `api-pagination`: Defines the universal pagination envelope contract, query parameter controls, metadata calculation, and HATEOAS navigation link generation across collection endpoints.

## Impact

- **API & Presentation**:
  - `src/presentation/schemas/pagination.py`: Defines `PaginationParams`, `PaginationMeta`, `PaginationLinks`, and generic `PaginatedResponse[T]`.
  - `src/presentation/api/v1/allocation_router.py`: Wrap `GET /contracts` and `GET /measurements` in `PaginatedResponse`.
  - `src/presentation/api/v1/budgeting_router.py`: Wrap `GET /cost-centers` in `PaginatedResponse`.
- **Application Layer**:
  - `src/allocation/application/use_cases/list_contracts.py`: Support `page` and `per_page`, returning items and total count.
  - `src/allocation/application/use_cases/list_measurements.py`: Support `page` and `per_page`, returning items and total count.
  - `src/budgeting/application/use_cases/`: Update cost center listing use case with pagination support.
- **Domain & Infrastructure Repositories**:
  - Repositories provide pagination offsets and counts for `ContractRepository`, `MeasurementRepository`, and `CostCenterRepository`.
- **Tests**:
  - API and unit tests updated to validate the `{ data, pagination, links }` contract and edge cases (first page, middle page, last page, empty results, boundary parameters).

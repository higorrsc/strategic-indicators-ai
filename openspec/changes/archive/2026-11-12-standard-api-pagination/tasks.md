# Tasks: Standardized API Pagination

## 1. Presentation Schema and Link Builder Utilities

- [x] 1.1 Create `src/presentation/schemas/pagination.py` defining `PaginationMeta`, `PaginationLinks`, `PaginatedResponse[T]`, and pagination query parameters
- [x] 1.2 Implement link builder utility `build_pagination_links` preserving query parameters and verify with unit tests in `tests/unit/presentation/test_pagination_links.py`

## 2. Domain & Application Layer Pagination Support

- [x] 2.1 Add pagination support to `ContractRepository` and `MeasurementRepository` (in-memory and SQLAlchemy) and verify with tests
- [x] 2.2 Update `ListContractsUseCase` to accept pagination and return `PaginatedResult[ContractDTO]` and verify with unit tests
- [x] 2.3 Update `ListMeasurementsUseCase` to accept pagination and return `PaginatedResult[MeasurementDTO]` and verify with unit tests

## 3. Router Integration and Verification

- [x] 3.1 Update `GET /api/v1/contracts` in `src/presentation/api/v1/allocation_router.py` to return `PaginatedResponse[ContractResponse]`
- [x] 3.2 Update `GET /api/v1/measurements` in `src/presentation/api/v1/allocation_router.py` to return `PaginatedResponse[MeasurementResponse]`
- [x] 3.3 Update `GET /api/v1/cost-centers` in `src/presentation/api/v1/budgeting_router.py` to return `PaginatedResponse[CostCenterResponse]`
- [x] 3.4 Update API tests in `tests/api/test_api_allocation.py` and `tests/api/test_api_budgeting.py` to validate paginated envelopes, links, and boundary conditions
- [x] 3.5 Run full regression suite, linter, formatter, and type checks (`uv run ruff check .`, `uv run ruff format --check .`, `uv run pyrefly check`, `uv run pytest`)

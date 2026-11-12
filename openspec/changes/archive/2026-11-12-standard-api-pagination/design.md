# Design: Standardized API Pagination

## Context

Collection endpoints in `allocation_router` (`/contracts`, `/measurements`) and `budgeting_router` (`/cost-centers`) previously returned flat JSON arrays (`list[ContractResponse]`). As the number of registered contracts, cost centers, and monthly measurements grows, unbounded responses create payload bloat and memory pressure.

See `proposal.md` for motivation and user requirement.

## Goals / Non-Goals

**Goals:**

- Provide a generic, strongly-typed Pydantic model `PaginatedResponse[T]` following the user's exact envelope schema:
  - `data: list[T]`
  - `pagination: PaginationMeta` (`page`, `perPage`, `totalItems`, `totalPages`)
  - `links: PaginationLinks` (`self`, `first`, `last`, `next`, `prev`)
- Encapsulate link generation helper that inspects the current request URL, path, and query params (`Request.url`) and replaces `page` and `perPage`.
- Support repository-level pagination (`limit` and `offset`) and count methods in both InMemory and SQLAlchemy repositories.
- Keep use cases Clean Architecture compliant by returning a paginated result DTO (`PaginatedResultDTO[T]` or `(items, total_count)` tuple).

**Non-Goals:**

- Cursor-based / keyset pagination (relational entity IDs and stable sorting by creation or code are sufficient for current corporate reporting scale).
- Breaking existing non-collection endpoints (such as detail lookups, indicators summary, or simulations).

## Decisions

### 1. Presentation-Level Generic Envelope `PaginatedResponse[T]`

- **Decision**: Define generic Pydantic model `PaginatedResponse[T]` where `data` is `list[T]`.
- **Rationale**: FastAPI seamlessly supports generic Pydantic models with OpenAPI/Swagger schema generation (e.g. `response_model=PaginatedResponse[ContractResponse]`).
- **Alternatives Considered**:
  - Custom dictionary serialization without Pydantic schemas: loses automatic Swagger documentation and response validation.

### 2. URL and Link Construction via FastAPI `Request`

- **Decision**: Create a reusable dependency or utility function `build_pagination_links(request: Request, page: int, per_page: int, total_pages: int) -> PaginationLinks`.
- **Rationale**: Reads `request.url.path` and `request.query_params`, dynamically constructing `self`, `first`, `last`, `next`, and `prev` relative or absolute URLs while preserving arbitrary domain query filters (e.g., `period`, `supplier_id`, `state`).
- **Alternatives Considered**:
  - Hardcoding endpoint paths in routers: brittle, duplicates link formatting logic across every router.

### 3. Application Layer `PaginationQuery` Value Object / DTO

- **Decision**: Define `PaginationQuery(page: int = 1, per_page: int = 20)` with helper property `offset = (page - 1) * per_page`.
- **Rationale**: Keeps database pagination math (`offset`, `limit`) encapsulated and decoupled from presentation frameworks.

### 4. Mathematical Handling of Empty Results

- **Decision**: When `totalItems == 0`, `totalPages = 0`, `next = None`, `prev = None`. When `totalItems > 0`, `totalPages = math.ceil(totalItems / perPage)`.
- **Rationale**: Avoids division by zero and provides accurate metadata for client rendering.

## Risks / Trade-offs

- **[Risk] Breaking Change for Existing Consumers Expecting Bare Array**: Clients parsing `response.json()` as a list will fail if expecting a top-level array.
  - *Mitigation*: The project is in early development / preview stage, and standardizing collection envelopes early avoids technical debt before mobile/frontend integration.

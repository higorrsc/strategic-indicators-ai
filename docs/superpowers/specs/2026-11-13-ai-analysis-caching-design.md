# Design Document: AI Analysis Caching, Smart Invalidation & Scoped Executive Summary

- **Date:** 2026-11-13
- **Author:** Antigravity & higorrsc
- **Status:** Under Review (Approved Scope: Scenario B)
- **Target Context:** `src/intelligence` (Strategic Intelligence) & `src/presentation`

---

## 1. Intent and The "Why"

Generating executive summaries, root cause analyses, and strategic recommendations via AI agents (LLMs) consumes tokens, introduces operational costs, and adds round-trip network latency. In business operations, multiple analysts and executives often query identical or focused perspectives (e.g., period, language locale, specific cost centers, or accounting accounts) within short timeframes.

Additionally, financial data is mutable:

1. **Identical queries on unchanged data** should be served instantly from storage without calling the LLM.
2. **Expired queries (TTL > 24h)** must be renewed to capture potential temporal re-evaluations.
3. **Underlying financial data drift** (e.g., new contract measurements, changed budget allocations, or newly detected anomalies) must immediately invalidate the cache even if 24 hours have not passed.
4. **On-demand refresh** (`force_refresh=true`) must allow users to bypass the cache when needed.
5. **Dimensional scoping** (by `cost_center_id` and/or `accounting_account_id`) allows targeted executive analysis without analyzing the entire company when only a specific division or accounting group is under review.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals

- **Scoped Intelligence:** Allow generating executive summaries scoped by entire period, specific `cost_center_id`, and/or specific `accounting_account_id`.
- **Token Efficiency & Sub-50ms Latency:** Serve previously generated AI summaries with 0 LLM token consumption on cache hits.
- **Configurable 24-Hour TTL:** Automatically expire analysis after 24 hours (configurable via `AI_CACHE_TTL_HOURS` in settings).
- **Automated Data Drift Invalidation:** Automatically detect data shifts via deterministic SHA-256 fingerprints of the scoped indicators and anomalies.
- **Forced Refresh Option:** Support `force_refresh: bool = False` across REST endpoints and use cases.
- **Transparent Status Propagation:** Expose `X-Cache-Status` header and schema field with explicit states: `HIT`, `MISS`, `EXPIRED`, `INVALIDATED_DRIFT`, `FORCED_REFRESH`.
- **Clean Architecture & SOLID:** Isolate caching in the domain and application layers with SQLAlchemy database persistence and in-memory test doubles.

### Non-Goals

- Real-time invalidation via external message brokers (Kafka/RabbitMQ).
- External Redis infrastructure dependency (PostgreSQL handles persistence cleanly with zero additional infrastructure).
- Background scheduled pre-warming of all possible filter combinations.

### Anti-Goals

- **No Stale Financial Diagnostics:** Never serve a cached analysis whose underlying input data hash differs from current financial data.
- **No Provider Coupling:** The caching mechanism remains decoupled from the AI provider (Ollama, OpenAI, Google, Fake).

---

## 3. Approaches Considered

| Approach | Description | Pros | Cons / Trade-offs | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **1. PostgreSQL Table + Data Hash + TTL + Force Refresh (Scenario B)** | Scoped queries (CC / Accounting Account) persisted in PostgreSQL with a deterministic SHA-256 fingerprint of the scoped inputs + `expires_at` timestamp. | Decoupled bounded contexts; survives restarts; handles data changes without event buses; zero extra infrastructure; provides targeted scoping. | Slightly higher initial scope to support optional filters in intelligence use cases. | **Chosen** (Best fit for Clean Architecture & user requirements) |
| **2. Event-Driven Cache Eviction** | Invalidate cache on domain events (`MeasurementAdded`, `BudgetUpdated`). | Read path doesn't compute data hash. | High coupling between bounded contexts; misses changes made via direct SQL/seeds/migrations; complex event bus. | Rejected |
| **3. External Redis Store** | Key-value store with native TTL. | Fast in-memory lookup. | Extra infrastructure dependency to run and maintain; volatile unless persistence configured. | Rejected |

---

## 4. Architectural Design & Boundaries

### 4.1 Domain Layer (`src/intelligence/domain/`)

#### 4.1.1 Entities & Value Objects

- **Enum `CacheStatus`**:
  - Values: `HIT`, `MISS`, `EXPIRED`, `INVALIDATED_DRIFT`, `FORCED_REFRESH`
- **Entity `AIAnalysisCache`**:
  - `id: UUID`
  - `cache_key: str` (e.g. `summary:period=2026-11:lang=pt-br:cc=UUID|all:acc=UUID|all`)
  - `period: Period`
  - `language: SupportedLanguage`
  - `cost_center_id: UUID | None`
  - `accounting_account_id: UUID | None`
  - `data_hash: str` (SHA-256 hex digest)
  - `executive_summary_payload: dict` (serialized DTO content)
  - `created_at: datetime`
  - `expires_at: datetime`
  - `updated_at: datetime`
  - **Methods**:
    - `evaluate_status(current_data_hash: str, force_refresh: bool, now: datetime) -> CacheStatus`:
      - If `force_refresh` is True -> `FORCED_REFRESH`
      - If `self.data_hash != current_data_hash` -> `INVALIDATED_DRIFT`
      - If `now >= self.expires_at` -> `EXPIRED`
      - Else -> `HIT`
    - `renew(current_data_hash: str, new_payload: dict, ttl_hours: int, now: datetime) -> None`

---

### 4.2 Application Layer (`src/intelligence/application/`)

#### 4.2.1 Repository Port (`ports/ai_analysis_cache_repository.py`)

```python
class AIAnalysisCacheRepository(Protocol):
    async def get_by_key(self, cache_key: str) -> AIAnalysisCache | None: ...
    async def save(self, cache: AIAnalysisCache) -> None: ...
    async def delete_by_key(self, cache_key: str) -> None: ...
```

#### 4.2.2 Hasher Service (`services/data_fingerprint_service.py`)

Deterministic SHA-256 generation combining:

1. Scope parameters: `period`, `language`, `cost_center_id`, `accounting_account_id`.
2. Scoped indicators summary: list of `(cost_center_id, budgeted_amount, actual_amount, variance, execution_rate, status)`.
3. Scoped anomalies: list of `(measurement_id, contract_id, cost_center_id, anomaly_type, severity, baseline_pct, actual_pct)`.

#### 4.2.3 Use Case Enhancement (`GenerateExecutiveSummaryUseCase`)

- **Query DTO / Signature**:

  ```python
  async def execute(
      self,
      period: Period,
      language: SupportedLanguage = SupportedLanguage.PT_BR,
      cost_center_id: UUID | None = None,
      accounting_account_id: UUID | None = None,
      force_refresh: bool = False,
  ) -> ExecutiveSummaryDTO:
  ```

- **Execution Flow**:
  1. Retrieve indicators and filter by `cost_center_id` and/or `accounting_account_id` if provided.
  2. Retrieve period anomalies and filter by `cost_center_id` and/or `accounting_account_id` if provided.
  3. Compute `current_data_hash` from the scoped indicators and anomalies.
  4. Generate `cache_key = f"summary:p={period}:l={language.value}:cc={cost_center_id or 'all'}:acc={accounting_account_id or 'all'}"`.
  5. Check repository: `existing_cache = await self._cache_repo.get_by_key(cache_key)`.
  6. Determine status:
     - If `existing_cache is None`: status is `FORCED_REFRESH` if `force_refresh` else `MISS`.
     - Else: status is `existing_cache.evaluate_status(current_data_hash, force_refresh, now=utc_now())`.
  7. **Cache Hit Path (`status == CacheStatus.HIT`)**:
     - Deserialize `existing_cache.executive_summary_payload` into `ExecutiveSummaryDTO`.
     - Set `dto.cache_status = CacheStatus.HIT`, `dto.is_cached = True`, `dto.cached_at = existing_cache.created_at`.
     - Return DTO immediately (zero LLM calls).
  8. **Cache Refresh/Miss Path (`status in (MISS, EXPIRED, INVALIDATED_DRIFT, FORCED_REFRESH)`)**:
     - Invoke `self._ai_port.generate_executive_summary(...)` with scoped indicators and anomalies.
     - On `AIProviderError`: invoke fallback template generation as currently implemented.
     - Build `ExecutiveSummaryDTO` with `cache_status = status`, `is_cached = False`.
     - Create or update `AIAnalysisCache` with `expires_at = now + timedelta(hours=settings.AI_CACHE_TTL_HOURS)`.
     - Persist via `await self._cache_repo.save(cache_entity)`.
     - Return DTO.

---

### 4.3 Infrastructure Layer (`src/intelligence/infrastructure/`)

#### 4.3.1 Database Model (`models.py`)

- Table: `ai_analysis_cache`
- Columns:
  - `id: Mapped[uuid.UUID]` (Primary Key, default=uuid4)
  - `cache_key: Mapped[str]` (String(255), unique=True, index=True)
  - `period: Mapped[str]` (String(7), index=True)
  - `language: Mapped[str]` (String(10))
  - `cost_center_id: Mapped[uuid.UUID | None]` (Uuid, nullable=True, index=True)
  - `accounting_account_id: Mapped[uuid.UUID | None]` (Uuid, nullable=True, index=True)
  - `data_hash: Mapped[str]` (String(64), nullable=False)
  - `summary_payload: Mapped[dict]` (JSON/JSONB, nullable=False)
  - `created_at: Mapped[datetime]` (DateTime(timezone=True), nullable=False)
  - `expires_at: Mapped[datetime]` (DateTime(timezone=True), nullable=False, index=True)
  - `updated_at: Mapped[datetime]` (DateTime(timezone=True), nullable=False)

#### 4.3.2 Repositories

- `SqlAlchemyAIAnalysisCacheRepository`: Implements `AIAnalysisCacheRepository` with upsert capability.
- `InMemoryAIAnalysisCacheRepository`: Dict-backed repository for isolated, sub-millisecond unit tests.

#### 4.3.3 Alembic Migration

- Generates migration creating `ai_analysis_cache` with unique index on `cache_key` and index on `expires_at`.

---

### 4.4 Presentation Layer (`src/presentation/`)

#### 4.4.1 Endpoints

- `GET /api/v1/intelligence/executive-summary`
  - Query parameters:
    - `period: str` (e.g. `2026-11`, required)
    - `lang: SupportedLanguage = SupportedLanguage.PT_BR` (optional)
    - `cost_center_id: UUID | None = None` (optional)
    - `accounting_account_id: UUID | None = None` (optional)
    - `force_refresh: bool = False` (optional)
  - Response Header: `X-Cache-Status: HIT | MISS | EXPIRED | INVALIDATED_DRIFT | FORCED_REFRESH`
  - Response Schema:
    - `is_cached: bool`
    - `cache_status: str`
    - `cached_at: datetime | None`
- `GET /api/v1/intelligence/executive-summary/pdf`
  - Same query parameters.
  - Generates PDF using the cached or freshly generated summary and passes through the `X-Cache-Status` header.

---

## 5. Architectural Calls Made

1. **Precedence Rules for Status:**
   - `force_refresh=True` always returns `FORCED_REFRESH`.
   - Data mismatch takes precedence over expiration: if a cache entry is expired AND data has changed, it is reported as `INVALIDATED_DRIFT` (highlighting to the user/analyst that data changed).
2. **Fallback Behavior on AI Failure:**
   - In case of `AIProviderError`, deterministic fallback remains the standard behavior (`is_fallback=True`). Expired or mismatched cache entries are not served as stale financial diagnostics.
3. **Settings Integration:**
   - Centralized `AI_CACHE_TTL_HOURS: int = 24` added to `Settings` (`pydantic-settings`).

---

## 6. What's Left to the Builder

- Exact index naming in Alembic migration (`ix_ai_analysis_cache_key`, `ix_ai_analysis_expires_at`).
- Minor JSON serialization mapping for `Decimal` / `Money` inside `summary_payload`.
- Specific test fixtures for mocking time in cache expiration tests.

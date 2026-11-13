# AI Analysis Caching & Scoped Executive Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement PostgreSQL-backed intelligent caching with 24-hour TTL, automatic data drift invalidation (SHA-256 fingerprint), on-demand forced refresh, and optional dimensional scoping (Cost Center & Accounting Account) for the Strategic Intelligence executive summary.

**Architecture:** Domain-Driven Design and Clean Architecture separating the core caching logic into domain entity/value objects (`AIAnalysisCache`, `CacheStatus`), application ports and fingerprinting services, infrastructure SQLAlchemy/in-memory repositories, and presentation FastAPI endpoints with `X-Cache-Status` headers.

**Tech Stack:** Python 3.15, FastAPI, SQLAlchemy (asyncio), PostgreSQL/SQLite, Pydantic v2, Pytest.

**Spec:** [`docs/superpowers/specs/2026-11-13-ai-analysis-caching-design.md`](file:///home/higorrsc/dev-disk/portfolio/strategic-indicators-ai/docs/superpowers/specs/2026-11-13-ai-analysis-caching-design.md)

## Global Constraints

- Domain entities must not depend on FastAPI, SQLAlchemy, Pydantic, or database drivers.
- All timestamps must be timezone-aware UTC (`datetime.now(timezone.utc)`).
- All commits must follow Conventional Commits and Gitmoji (e.g. `✨ feat(intelligence): ...`, `✅ test(intelligence): ...`).
- Repositories must isolate ORM models and never expose them to domain or application layers.
- Fast unit tests must use the in-memory repository fake without requiring database connections or Docker.

## Review Focus

- If `force_refresh=True` is provided on a cold cache (no existing entry), status must be `FORCED_REFRESH` and an entry must be saved.
- If data hash differs from stored hash, status must be `INVALIDATED_DRIFT` even if current time is within the 24-hour TTL.
- If data hash is unchanged but current time is past `expires_at`, status must be `EXPIRED` and the cache must be regenerated.
- If data hash is unchanged and current time is before `expires_at`, status must be `HIT` and 0 LLM calls must be made.
- If the AI provider fails (`AIProviderError`) during a cache refresh, the existing deterministic template fallback must be returned (`is_fallback=True`).

---

### Task 1: Domain Entities & Value Objects

**Files:**
- Create: `src/intelligence/domain/cache.py`
- Modify: `src/intelligence/domain/__init__.py`
- Test: `tests/unit/intelligence/test_cache_domain.py`

**Interfaces:**
- Produces:
  - `CacheStatus(str, Enum)`: `HIT = "HIT"`, `MISS = "MISS"`, `EXPIRED = "EXPIRED"`, `INVALIDATED_DRIFT = "INVALIDATED_DRIFT"`, `FORCED_REFRESH = "FORCED_REFRESH"`
  - `AIAnalysisCache`: entity with `id: UUID`, `cache_key: str`, `period: Period`, `language: SupportedLanguage`, `cost_center_id: UUID | None`, `accounting_account_id: UUID | None`, `data_hash: str`, `summary_payload: dict`, `created_at: datetime`, `expires_at: datetime`, `updated_at: datetime`
  - `AIAnalysisCache.evaluate_status(current_data_hash: str, force_refresh: bool, now: datetime) -> CacheStatus`
  - `AIAnalysisCache.renew(current_data_hash: str, new_payload: dict, ttl_hours: int, now: datetime) -> None`

- [x] **Step 1: Write the failing unit tests for domain cache evaluation**

```python
# tests/unit/intelligence/test_cache_domain.py
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from src.intelligence.domain.cache import AIAnalysisCache, CacheStatus
from src.shared.domain.value_objects import Period, SupportedLanguage


def test_should_return_hit_when_hash_matches_and_unexpired():
    now = datetime.now(timezone.utc)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    assert (
        cache.evaluate_status("hash_v1", force_refresh=False, now=now)
        == CacheStatus.HIT
    )


def test_should_return_invalidated_drift_when_hash_changes_even_if_unexpired():
    now = datetime.now(timezone.utc)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    assert (
        cache.evaluate_status("hash_v2", force_refresh=False, now=now)
        == CacheStatus.INVALIDATED_DRIFT
    )


def test_should_return_expired_when_time_past_ttl_and_hash_unchanged():
    now = datetime.now(timezone.utc)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=25),
        expires_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=25),
    )
    assert (
        cache.evaluate_status("hash_v1", force_refresh=False, now=now)
        == CacheStatus.EXPIRED
    )


def test_should_return_forced_refresh_when_force_flag_true():
    now = datetime.now(timezone.utc)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="hash_v1",
        summary_payload={"executive_summary": "ok"},
        created_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=23),
        updated_at=now - timedelta(hours=1),
    )
    assert (
        cache.evaluate_status("hash_v1", force_refresh=True, now=now)
        == CacheStatus.FORCED_REFRESH
    )
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/intelligence/test_cache_domain.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.intelligence.domain.cache'`

- [x] **Step 3: Implement domain models in `src/intelligence/domain/cache.py`**

Define `CacheStatus` enum and `AIAnalysisCache` dataclass with `evaluate_status` and `renew` methods.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/intelligence/test_cache_domain.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/intelligence/domain/ tests/unit/intelligence/test_cache_domain.py
git commit -m "✨ feat(intelligence): add AIAnalysisCache domain entity and CacheStatus enum"
```

---

### Task 2: Application Port, DTO Updates & Fingerprint Hasher Service

**Files:**
- Create: `src/intelligence/application/ports/ai_analysis_cache_repository.py`
- Create: `src/intelligence/application/services/data_fingerprint_service.py`
- Modify: `src/intelligence/application/dto.py`
- Modify: `src/shared/config/settings.py` (add `AI_CACHE_TTL_HOURS: int = 24`)
- Test: `tests/unit/intelligence/test_data_fingerprint_service.py`

**Interfaces:**
- Consumes: `AIAnalysisCache`, `CacheStatus` from Task 1
- Produces:
  - `AIAnalysisCacheRepository(Protocol)` with `get_by_key(cache_key: str) -> AIAnalysisCache | None`, `save(cache: AIAnalysisCache) -> None`, `delete_by_key(cache_key: str) -> None`
  - `compute_intelligence_data_hash(period: Period, language: SupportedLanguage, cost_center_id: UUID | None, accounting_account_id: UUID | None, indicators: list[Any], anomalies: list[Any]) -> str`
  - Updated `ExecutiveSummaryDTO`: adds `cache_status: CacheStatus = CacheStatus.MISS`, `is_cached: bool = False`, `cached_at: datetime | None = None`

- [x] **Step 1: Write the failing unit tests for `data_fingerprint_service`**

```python
# tests/unit/intelligence/test_data_fingerprint_service.py
from src.intelligence.application.services.data_fingerprint_service import (
    compute_intelligence_data_hash,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


def test_should_generate_deterministic_hash_for_identical_inputs():
    p = Period.from_string("2026-11")
    hash1 = compute_intelligence_data_hash(
        p, SupportedLanguage.PT_BR, None, None, [{"code": "CC1", "amount": 100}], []
    )
    hash2 = compute_intelligence_data_hash(
        p, SupportedLanguage.PT_BR, None, None, [{"code": "CC1", "amount": 100}], []
    )
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256


def test_should_change_hash_when_data_changes():
    p = Period.from_string("2026-11")
    hash1 = compute_intelligence_data_hash(
        p, SupportedLanguage.PT_BR, None, None, [{"code": "CC1", "amount": 100}], []
    )
    hash2 = compute_intelligence_data_hash(
        p, SupportedLanguage.PT_BR, None, None, [{"code": "CC1", "amount": 200}], []
    )
    assert hash1 != hash2
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/intelligence/test_data_fingerprint_service.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [x] **Step 3: Implement `DataFingerprintService`, port, and DTO additions**

Create `src/intelligence/application/ports/ai_analysis_cache_repository.py`, implement `compute_intelligence_data_hash` using `hashlib.sha256(json.dumps(..., sort_keys=True).encode())`, update `ExecutiveSummaryDTO`, and add `AI_CACHE_TTL_HOURS: int = 24` to `Settings`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/intelligence/test_data_fingerprint_service.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/intelligence/application/ src/shared/config/settings.py tests/unit/intelligence/test_data_fingerprint_service.py
git commit -m "✨ feat(intelligence): add AIAnalysisCacheRepository port and DataFingerprintService"
```

---

### Task 3: Infrastructure Persistence (SQLAlchemy & In-Memory Fake)

**Files:**
- Create: `src/intelligence/infrastructure/database/models.py`
- Create: `src/intelligence/infrastructure/repositories/sqlalchemy_ai_cache_repository.py`
- Create: `src/intelligence/infrastructure/repositories/in_memory_ai_cache_repository.py`
- Modify: `alembic/versions/` (create migration script for `ai_analysis_cache` table)
- Test: `tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py`

**Interfaces:**
- Consumes: `AIAnalysisCacheRepository` from Task 2, `AIAnalysisCache` from Task 1
- Produces:
  - `AIAnalysisCacheModel`: SQLAlchemy ORM model for `ai_analysis_cache` table
  - `SqlAlchemyAIAnalysisCacheRepository`: persistent implementation using `AsyncSession`
  - `InMemoryAIAnalysisCacheRepository`: in-memory dict fake for unit testing

- [x] **Step 1: Write integration tests for `SqlAlchemyAIAnalysisCacheRepository`**

```python
# tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from src.intelligence.domain.cache import AIAnalysisCache
from src.intelligence.infrastructure.repositories.sqlalchemy_ai_cache_repository import (
    SqlAlchemyAIAnalysisCacheRepository,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


@pytest.mark.asyncio
async def test_should_save_and_retrieve_cache_by_key(db_session):
    repo = SqlAlchemyAIAnalysisCacheRepository(db_session)
    now = datetime.now(timezone.utc)
    cache = AIAnalysisCache(
        id=uuid4(),
        cache_key="summary:p=2026-11:l=pt-br:cc=all:acc=all",
        period=Period.from_string("2026-11"),
        language=SupportedLanguage.PT_BR,
        cost_center_id=None,
        accounting_account_id=None,
        data_hash="abc123hash",
        summary_payload={"executive_summary": "Report text"},
        created_at=now,
        expires_at=now + timedelta(hours=24),
        updated_at=now,
    )
    await repo.save(cache)
    retrieved = await repo.get_by_key(cache.cache_key)
    assert retrieved is not None
    assert retrieved.cache_key == cache.cache_key
    assert retrieved.data_hash == "abc123hash"
    assert retrieved.summary_payload["executive_summary"] == "Report text"
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [x] **Step 3: Implement database model, repositories, and migration**

1. Create `AIAnalysisCacheModel` in `src/intelligence/infrastructure/database/models.py`.
2. Implement `SqlAlchemyAIAnalysisCacheRepository` with upsert/merge logic and domain mapping.
3. Implement `InMemoryAIAnalysisCacheRepository` with a dict storing `cache_key -> AIAnalysisCache`.
4. Generate/create migration script adding `ai_analysis_cache` table with unique index on `cache_key`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/intelligence/test_sqlalchemy_ai_cache_repository.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/intelligence/infrastructure/ alembic/ tests/integration/intelligence/
git commit -m "✨ feat(intelligence): implement SQLAlchemy and InMemory AI analysis cache repositories"
```

---

### Task 4: Use Case Enhancement with Scoping & Caching

**Files:**
- Modify: `src/intelligence/application/use_cases/generate_executive_summary.py`
- Modify: `src/intelligence/application/use_cases/analyze_allocation_anomalies.py` (add scoping filters for CC / Account)
- Test: `tests/unit/intelligence/test_executive_summary_caching.py`

**Interfaces:**
- Consumes: `AIAnalysisCacheRepository`, `compute_intelligence_data_hash`, `AIAnalysisCache`, `CacheStatus`
- Produces: Enhanced `GenerateExecutiveSummaryUseCase.execute(...)` supporting `cost_center_id`, `accounting_account_id`, and `force_refresh`

- [x] **Step 1: Write comprehensive unit tests for use case caching and scoping**

```python
# tests/unit/intelligence/test_executive_summary_caching.py
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from src.intelligence.application.use_cases.generate_executive_summary import (
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.infrastructure.fake_ai_adapter import FakeAIAdapter
from src.intelligence.infrastructure.repositories.in_memory_ai_cache_repository import (
    InMemoryAIAnalysisCacheRepository,
)
from src.shared.domain.value_objects import Period, SupportedLanguage


@pytest.mark.asyncio
async def test_should_call_ai_on_first_request_and_hit_cache_on_second(mock_deps):
    use_case, cache_repo, ai_port = mock_deps
    period = Period.from_string("2026-11")

    # First request: MISS -> calls AI
    result1 = await use_case.execute(period, language=SupportedLanguage.PT_BR)
    assert result1.is_cached is False
    assert result1.cache_status.value == "MISS"
    assert ai_port.call_count == 1

    # Second request: HIT -> uses cache, 0 AI calls
    result2 = await use_case.execute(period, language=SupportedLanguage.PT_BR)
    assert result2.is_cached is True
    assert result2.cache_status.value == "HIT"
    assert ai_port.call_count == 1  # No additional AI calls!


@pytest.mark.asyncio
async def test_should_force_refresh_when_flag_is_true(mock_deps):
    use_case, cache_repo, ai_port = mock_deps
    period = Period.from_string("2026-11")

    await use_case.execute(period)
    assert ai_port.call_count == 1

    # Force refresh
    result = await use_case.execute(period, force_refresh=True)
    assert result.is_cached is False
    assert result.cache_status.value == "FORCED_REFRESH"
    assert ai_port.call_count == 2
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/intelligence/test_executive_summary_caching.py -v`
Expected: FAIL

- [x] **Step 3: Implement scoping and caching orchestration in `GenerateExecutiveSummaryUseCase`**

1. Inject `cache_repo: AIAnalysisCacheRepository` into `__init__`.
2. Filter indicators and anomalies by `cost_center_id` and `accounting_account_id` if provided.
3. Compute `current_data_hash`.
4. Check cache, evaluate status, handle `HIT` with early return, or call `ai_port` and save cache on `MISS`/`EXPIRED`/`INVALIDATED_DRIFT`/`FORCED_REFRESH`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/intelligence/test_executive_summary_caching.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add src/intelligence/application/use_cases/ tests/unit/intelligence/test_executive_summary_caching.py
git commit -m "✨ feat(intelligence): add caching and scoping to GenerateExecutiveSummaryUseCase"
```

---

### Task 5: Presentation API, PDF Export & HTTP Response Headers

**Files:**
- Modify: `src/presentation/schemas/intelligence.py`
- Modify: `src/presentation/api/v1/intelligence_router.py`
- Modify: `src/presentation/dependencies.py` (wire `AIAnalysisCacheRepository`)
- Test: `tests/api/test_intelligence_caching_api.py`

**Interfaces:**
- Consumes: Enhanced `GenerateExecutiveSummaryUseCase` from Task 4
- Produces:
  - Updated `GET /api/v1/intelligence/executive-summary` with query params `cost_center_id`, `accounting_account_id`, `force_refresh`, schema fields `is_cached`, `cache_status`, `cached_at`, and header `X-Cache-Status`.
  - Updated `GET /api/v1/intelligence/executive-summary/pdf` passing `X-Cache-Status` header.

- [x] **Step 1: Write API integration tests verifying `X-Cache-Status` headers and schema**

```python
# tests/api/test_intelligence_caching_api.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_executive_summary_cache_headers_and_force_refresh(client: AsyncClient):
    # First call: MISS
    resp1 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br"
    )
    assert resp1.status_code == 200
    assert resp1.headers["X-Cache-Status"] == "MISS"
    data1 = resp1.json()
    assert data1["is_cached"] is False
    assert data1["cache_status"] == "MISS"

    # Second call: HIT
    resp2 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br"
    )
    assert resp2.status_code == 200
    assert resp2.headers["X-Cache-Status"] == "HIT"
    data2 = resp2.json()
    assert data2["is_cached"] is True
    assert data2["cache_status"] == "HIT"

    # Third call with force_refresh=true: FORCED_REFRESH
    resp3 = await client.get(
        "/api/v1/intelligence/executive-summary?period=2026-11&lang=pt-br&force_refresh=true"
    )
    assert resp3.status_code == 200
    assert resp3.headers["X-Cache-Status"] == "FORCED_REFRESH"
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_intelligence_caching_api.py -v`
Expected: FAIL

- [x] **Step 3: Update Presentation router, dependencies, and schemas**

1. Add `is_cached: bool = False`, `cache_status: str = "MISS"`, and `cached_at: datetime | None = None` to `ExecutiveSummaryResponseSchema`.
2. Add `cost_center_id`, `accounting_account_id`, `force_refresh` queries to `get_executive_summary` and `download_executive_summary_pdf`.
3. Set `response.headers["X-Cache-Status"] = result.cache_status.value`.
4. Provide repository in `src/presentation/dependencies.py`.

- [x] **Step 4: Run test to verify it passes**

Run: `pytest tests/api/test_intelligence_caching_api.py -v`
Expected: PASS

- [x] **Step 5: Run full project verification suite**

Run:
```bash
pytest
ruff check .
ruff format --check .
pyrefly check
```
Expected: All tests pass, 0 linter errors, 0 type errors.

- [x] **Step 6: Commit**

```bash
git add src/presentation/ tests/api/
git commit -m "✨ feat(api): expose cache metadata, force_refresh, and X-Cache-Status headers"
```

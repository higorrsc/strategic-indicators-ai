# Design: Strategic Budget Indicators System

## Context

The repository provides the baseline tooling (Python 3.15, `uv`, `ruff`, `pyrefly`, `pytest`, `openspec`). As defined in `AGENTS.md`, the architecture strictly adheres to **Clean Architecture** and **Domain-Driven Design (DDD)**. Domain logic must remain framework-agnostic and free from ORM or HTTP dependencies.

See `proposal.md` for background motivation and `specs/` for behavioral contracts.

## Goals / Non-Goals

**Goals:**

- Implement modular bounded contexts: `budgeting`, `cost-allocation`, `budget-indicators`, and `strategic-intelligence`.
- Enforce strict monetary domain invariants (exact penny allocation closing to 100%, cycle-free cost center trees).
- Provide an extensible `AIPort` interface implemented with Pydantic AI supporting interchangeable providers:
  - Local inference: Ollama (OpenAI-compatible local server `http://localhost:11434/v1`);
  - Cloud inference: Google Gemini (`google-gla`) and OpenAI (`openai`).
- Expose typed FastAPI REST endpoints with OpenAPI 3.1 specifications.
- Provide comprehensive test coverage: pure unit domain tests, use case tests with fakes, and BDD acceptance tests (`pytest-bdd`).

**Non-Goals:**

- Real-time streaming or WebSocket synchronization (standard HTTP REST with SSE if needed later is sufficient).
- Frontend UI implementation (Streamlit or React dashboard can consume the public API in subsequent changes).
- Multi-tenant enterprise SSO (simple API key or bearer token auth is sufficient for initial contracts).

## Architecture & Component Diagram

```text
Presentation Layer (FastAPI Controllers & Pydantic Schemas)
       │
       ▼
Application Layer (Use Cases, DTOs, Ports)
       │
       ├──────────────────────────────┬──────────────────────────────┐
       ▼                              ▼                              ▼
Domain: budgeting             Domain: cost-allocation        Domain: budget-indicators
 (CostCenter, Budget,          (Contract, Supplier,           (VarianceCalculator,
  CostCenterHierarchy)          Measurement, AllocationRule,   WhatIfSimulator)
                                ExactPennyAllocator)
                                      │
                                      ▼
                             Domain: strategic-intelligence
                              (AllocationAnomalyDetector,
                               AIPort: ExecutiveSummary & Scenario)
                                      │
       ┌──────────────────────────────┴──────────────────────────────┐
       ▼                                                             ▼
Infrastructure: Persistence                                  Infrastructure: AI
 (SQLAlchemy Async Repositories,                              (PydanticAIAdapter:
  In-Memory Test Doubles, Unit of Work)                        Ollama / Google / OpenAI)
```

## Decisions

### 1. Bounded Context Modular Directory Layout

- **Decision**: Structure `src/` by modular domain contexts (`src/budgeting`, `src/allocation`, `src/indicators`, `src/intelligence`, `src/shared`) rather than generic global horizontal folders.
- **Rationale**: Isolates domain models and allows independent evolution. Shared value objects (`Money`, `Period`, `Percentage`) live in `src/shared/domain/`.
- **Alternatives Considered**: Global single `domain/`, `application/`, `infrastructure/` folders — rejected due to coupling and cluttered entity directories as features scale.

### 2. Multi-Provider AI Architecture via Ports and Adapters

- **Decision**: Define a domain protocol `AIPort` in `intelligence/application/ports/ai_port.py`. Implement `PydanticAIAdapter` utilizing Pydantic AI's `Agent` parameterized by `pydantic-settings` (`AI_PROVIDER`, `AI_MODEL`, `AI_BASE_URL`).
- **Rationale**: Keeps domain and application use cases 100% decoupled from LLM SDKs. Enables offline deterministic testing using `FakeAIPort` and zero external API dependencies.
- **Provider Support**:
  - `ollama`: Uses Ollama's local OpenAI-compatible endpoint (e.g. `llama3.2`, `mistral`, `qwen2.5`) with zero cloud egress.
  - `google`: Uses `google-gla` with Gemini models.
  - `openai`: Uses official OpenAI endpoints.
- **Alternatives Considered**: Direct SDK calls inside controllers — rejected by Clean Architecture rules.

### 3. Monetary Representation and Penny Reconciliation

- **Decision**: Represent monetary amounts using a dedicated `Money` Value Object backed by `decimal.Decimal` with 2 decimal places and rounding mode `ROUND_HALF_UP`.
- **Rationale**: Floating-point numbers introduce subtle precision bugs. When splitting odd amounts across cost centers (e.g., $100.00 across 3 centers), the `ExactPennyAllocator` domain service allocates calculated cents and assigns any remainder cent to the primary allocation line so the sum equals the gross amount exactly.
- **Alternatives Considered**: Storing integer cents without a Value Object — rejected because value objects encapsulate currency validation and arithmetic rules cleanly.

### 4. Deterministic Simulation Engine

- **Decision**: Implement `WhatIfSimulator` as a pure domain service that receives existing period snapshots, clones them in-memory, applies delta parameters, and recalculates all indicators without database writes.
- **Rationale**: Fast, stateless, idempotent, and thread-safe.

## Risks / Trade-offs

- **[Risk: Local LLM Latency / Resource Constraints]** → Mitigation: All AI generation calls run asynchronously with configurable timeouts (default 30s). When timeouts or errors occur, the application falls back gracefully, delivering deterministic indicators with an explicit error alert flag.
- **[Risk: Deep Tree Hierarchy Performance]** → Mitigation: Cost centers utilize materialized path or adjacency list models with depth limits (maximum 10 levels) and cycle detection in domain entities.
- **[Risk: Non-deterministic LLM JSON schema compliance]** → Mitigation: Pydantic AI enforces runtime schema validation against Pydantic output models. If output validation fails, retries are configured and captured before falling back.

## Open Questions

None. Core scope, domain boundaries, invariants, and multi-provider AI requirements are established.

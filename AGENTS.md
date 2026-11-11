# AGENTS.md

## Project Development Guidelines

This repository contains Python web applications designed according to **SOLID**, **Domain-Driven Design (DDD)**, and **Clean Architecture** principles.

The AI agent must treat this document as the primary development guideline for the repository and must preserve the architectural boundaries defined here.

The goal is to produce software that is:

- maintainable;
- testable;
- modular;
- framework-independent at the domain level;
- strongly typed;
- observable;
- documented;
- easy to evolve;
- suitable for incremental development by human developers and AI agents.

---

# 1. General Principles

The following principles are mandatory unless a project-specific requirement explicitly overrides them.

## 1.1 SOLID

Code must follow:

- **Single Responsibility Principle**
- **Open/Closed Principle**
- **Liskov Substitution Principle**
- **Interface Segregation Principle**
- **Dependency Inversion Principle**

Avoid:

- god classes;
- god functions;
- large conditional blocks;
- duplicated business rules;
- framework-dependent domain logic;
- infrastructure dependencies inside domain entities;
- unnecessary abstractions.

Do not create abstractions merely to satisfy SOLID.

An abstraction must exist because:

1. there is a meaningful contract;
2. there are multiple implementations;
3. the dependency must be inverted;
4. the dependency must be isolated for testing;
5. the business domain requires the abstraction.

---

# 2. Clean Architecture

The application must be organized around business rules rather than frameworks.

The preferred dependency direction is:

```text
Presentation
     ↓
Application
     ↓
Domain
     ↑
Infrastructure
```

The inner layers must never depend on the outer layers.

In particular:

```text
Domain
  MUST NOT depend on:
    Django
    FastAPI
    SQLAlchemy
    Pydantic
    Streamlit
    HTTP
    database drivers
    external APIs
    filesystem
```

Application/use-case code should depend on abstractions rather than infrastructure implementations.

Infrastructure implements the abstractions defined by the inner layers.

---

# 3. Suggested Architecture

The exact directory structure may vary according to the project, but the conceptual structure must remain consistent.

For non-Django applications:

```text
src/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── services/
│   ├── repositories/
│   ├── exceptions/
│   └── ...
│
├── application/
│   ├── use_cases/
│   ├── dto/
│   ├── ports/
│   └── ...
│
├── infrastructure/
│   ├── database/
│   │   ├── models/
│   │   ├── repositories/
│   │   └── migrations/
│   ├── external_services/
│   └── ...
│
├── presentation/
│   ├── api/
│   │   ├── controllers/
│   │   ├── schemas/
│   │   └── dependencies/
│   └── ...
│
└── main.py
```

An alternative modular structure is acceptable when the domain naturally requires bounded contexts:

```text
src/
├── _shared/
├── access/
├── contract/
├── measurement/
├── vendor/
└── ...
```

The important requirement is that architectural boundaries remain explicit.

---

# 4. Domain Layer

The domain layer contains the application's business rules.

It may contain:

- Entities;
- Value Objects;
- Aggregates;
- Domain Services;
- Domain Events;
- Repository interfaces;
- Domain exceptions;
- business policies;
- business specifications.

The domain must not know how persistence, HTTP, authentication infrastructure, AI providers, or frameworks work.

## 4.1 Entities

Entities must encapsulate business invariants.

Prefer behavior over anemic data structures.

Avoid:

```python
entity.status = "approved"
```

when the transition represents a business rule.

Prefer:

```python
entity.approve()
```

when approval is a domain operation.

## 4.2 Value Objects

Use Value Objects when a concept has:

- validation rules;
- semantic meaning;
- identity independent of the database;
- behavior associated with the value.

Examples:

```text
Money
Percentage
EmployeeId
ContractId
CostCenterId
Email
MeasurementPeriod
```

## 4.3 Domain Services

Use a Domain Service when a business rule:

- does not naturally belong to a single Entity;
- operates over multiple domain objects;
- represents a meaningful domain operation.

Do not use Domain Services as generic utility classes.

---

# 5. Application Layer

The Application Layer orchestrates use cases.

A Use Case should:

1. receive input;
2. validate application-level requirements;
3. load required domain objects;
4. invoke domain behavior;
5. coordinate repositories/services;
6. persist changes;
7. return an application result.

A Use Case must not contain infrastructure details.

Example conceptual flow:

```text
Controller
    ↓
Input DTO
    ↓
Use Case
    ↓
Domain
    ↓
Repository Interface
    ↓
Infrastructure Repository
```

Use Cases must be independently testable without:

- HTTP;
- Django;
- FastAPI;
- SQLAlchemy;
- a real database;
- Streamlit;
- external APIs.

---

# 6. DTOs and Pydantic

Pydantic is the standard mechanism for validation and data transfer at application/presentation boundaries.

Use Pydantic for:

- API request schemas;
- API response schemas;
- configuration;
- external service contracts;
- application DTOs when appropriate.

Do not make Pydantic models the domain model merely for convenience.

The domain should not become dependent on Pydantic unless there is a strong architectural reason.

Example:

```text
HTTP Request
    ↓
Pydantic Request Schema
    ↓
Application DTO
    ↓
Use Case
    ↓
Domain Entity
```

---

# 7. Pydantic Settings

Application configuration must be centralized.

Use:

```text
pydantic-settings
```

for environment-based configuration.

Configuration must not be scattered through the application.

Avoid:

```python
os.getenv("DATABASE_URL")
```

throughout the codebase.

Prefer a centralized settings object.

Secrets must come from environment variables or secret management infrastructure.

Never commit:

- passwords;
- API keys;
- tokens;
- certificates;
- private keys;
- production credentials.

---

# 8. Dependency Injection

Dependencies must be injected rather than instantiated inside business logic.

Avoid:

```python
class SomeUseCase:
    def __init__(self):
        self.repository = SqlAlchemyRepository()
```

Prefer:

```python
class SomeUseCase:
    def __init__(self, repository: SomeRepository):
        self.repository = repository
```

The composition root is responsible for connecting abstractions to implementations.

---

# 9. Repositories

Repositories represent persistence abstractions required by the application/domain.

Example:

```python
class EmployeeRepository(Protocol):
    async def get_by_id(self, employee_id: UUID) -> Employee | None: ...
```

The domain/application layer defines the contract.

Infrastructure implements it:

```text
domain/application
        ↓
Repository Interface
        ↑
SQLAlchemy Repository
```

Repositories must not expose ORM models to the domain.

---

# 10. Database

## 10.1 SQLAlchemy Projects

For projects that do not use Django:

- SQLAlchemy must be used asynchronously;
- Alembic must manage migrations;
- repositories must isolate SQLAlchemy;
- ORM models must remain in infrastructure;
- domain entities must not inherit from SQLAlchemy classes.

Preferred:

```text
Domain Entity
    ↕
Repository
    ↕
SQLAlchemy Model
```

Avoid:

```text
Domain Entity == SQLAlchemy Model
```

unless there is a documented architectural reason.

## 10.2 Transactions

Transaction boundaries must be explicit.

A Use Case should not unexpectedly create multiple independent transactions.

Use a Unit of Work abstraction when the use case requires atomic operations across repositories.

Example:

```text
Use Case
   ↓
Unit of Work
   ├── Repository A
   ├── Repository B
   └── commit()
```

---

# 11. Django Projects

Django is allowed to provide:

- HTTP infrastructure;
- authentication infrastructure;
- admin interface;
- ORM;
- migrations;
- framework integrations.

Django must not become the location of business rules merely because it provides Models, Views, Forms, or Services.

Business rules must remain in:

```text
Domain
Application / Use Cases
```

Django Models should primarily represent persistence concerns.

Django Views should:

1. receive the request;
2. translate input;
3. invoke the appropriate Use Case;
4. translate the result into an HTTP response.

Avoid putting business rules directly into:

```text
views.py
models.py
serializers.py
admin.py
```

unless the rule is specifically related to framework/persistence/presentation behavior.

---

# 12. API Architecture

For FastAPI applications, use:

```text
Router
   ↓
Controller / Application Adapter
   ↓
Use Case
   ↓
Domain
```

FastAPI dependencies are responsible for composition and infrastructure wiring.

Do not put business rules inside route functions.

API schemas must explicitly define:

- input;
- output;
- validation;
- error contracts.

HTTP status codes must represent application outcomes consistently.

---

# 13. Uvicorn

Uvicorn is the ASGI application server.

It must not leak into domain/application code.

Local development may use:

```text
uvicorn
```

Production execution should be defined by the deployment architecture.

---

# 14. Streamlit

Streamlit is a presentation client.

It must not contain business rules.

The preferred architecture is:

```text
Streamlit
    ↓
HTTP API
    ↓
Application
    ↓
Domain
```

The Streamlit application should consume API contracts rather than access the database directly.

---

# 15. Project-Specific Architecture

## 15.1 Supply Chain Anomaly Management

The application manages stock movement processing and anomaly detection.

Core domain concepts may include:

```text
StockMovement
Product
Warehouse
MovementHistory
HistoricalStatistics
Anomaly
AnomalyAlert
```

The domain must contain the rules for anomaly detection.

Examples:

- historical standard deviation;
- moving averages;
- deviation thresholds;
- unexpected outbound peaks;
- abnormal inbound behavior;
- anomaly classification.

The statistical calculation itself may be implemented as a Domain Service when it represents a business rule.

Example:

```text
StockMovement
      ↓
Historical Analysis
      ↓
Deviation Calculation
      ↓
Anomaly Detection
      ↓
Anomaly Alert
```

The Streamlit application consumes the API and is responsible only for visualization and user interaction.

The anomaly algorithm must be independently testable without Streamlit or HTTP.

---

# 16. Competency Analysis

The application uses Django for:

- administrative interfaces;
- authentication integration where appropriate;
- persistence;
- complex relational queries;
- Django Admin.

The business architecture remains Clean Architecture.

Example domain:

```text
Employee
   ↓
Assessment
   ↓
Competency
   ↓
Competency Track
```

The competency gap calculation must be implemented in a Use Case/domain service.

For example:

```text
Current Competency
        ↓
Required Competency
        ↓
Gap Calculation
        ↓
Development Recommendation
```

Do not implement this logic directly in:

```text
Django View
Django Model
Django Admin
Django Serializer
```

The Django layer is an adapter.

---

# 17. Strategic Indicators with SDD and AI

This project must follow **Spec-Driven Development**.

The specification is the source of truth.

Preferred development sequence:

```text
Requirement
    ↓
Specification
    ↓
API Contract
    ↓
Acceptance Tests
    ↓
Implementation
    ↓
Automated Tests
    ↓
Refactoring
```

The agent must not invent behavior that is not defined by the specification when implementing a feature.

## 17.1 API Specification

Prefer OpenAPI for API contracts.

The specification should define:

- endpoints;
- HTTP methods;
- parameters;
- request schemas;
- response schemas;
- error responses;
- authentication requirements;
- acceptance criteria.

Pydantic models should remain consistent with the API specification.

## 17.2 BDD

When BDD is appropriate, use:

```text
pytest-bdd
```

or:

```text
behave
```

Acceptance criteria should describe observable behavior.

Example:

```text
Given historical process data exists
When the indicator is requested
Then the API returns the calculated indicator
And the response follows the documented schema
```

## 17.3 AI

Pydantic AI may be used for AI-powered use cases.

AI integration must be isolated behind application/domain abstractions when possible.

Do not allow an LLM provider to become a hard dependency of unrelated business logic.

Prefer:

```text
Use Case
    ↓
AI Port
    ↓
Pydantic AI Adapter
    ↓
LLM Provider
```

The AI response must be validated.

Never assume an LLM response is structurally correct.

Use typed output schemas whenever possible.

AI-generated insights must be distinguishable from deterministic business calculations.

---

# 18. AI Agent Development Workflow

When an AI coding agent is used, the agent must follow:

```text
1. Read AGENTS.md
2. Read project specification
3. Inspect existing architecture
4. Identify affected bounded context
5. Identify acceptance criteria
6. Write/update tests
7. Implement domain logic
8. Implement use case
9. Implement infrastructure
10. Implement presentation
11. Run tests
12. Run formatter
13. Run linter
14. Run type checker
15. Review architecture
16. Refactor if necessary
```

The agent must not bypass tests to make an implementation appear successful.

If a test fails:

```text
Test Failure
    ↓
Analyze error
    ↓
Identify root cause
    ↓
Fix implementation
    ↓
Run affected tests
    ↓
Run complete suite
```

Do not blindly modify tests to accommodate incorrect implementation.

---

# 19. Testing Strategy

Testing is mandatory.

Every feature must consider at least:

```text
Happy Path
Unhappy Path
Boundary Cases
Invalid Input
Business Rule Violations
Infrastructure Failures
```

The exact test pyramid should prioritize fast tests.

Preferred structure:

```text
        E2E
       /   \
    API/BDD
    /     \
 Integration
     |
   Unit
```

Most business behavior should be covered by unit tests.

---

# 20. Happy Path

Happy-path tests validate valid business scenarios.

Example:

```text
Given a valid stock movement
And sufficient historical data
When anomaly detection runs
Then the expected anomaly classification is returned
```

Tests must verify behavior, not implementation details.

---

# 21. Unhappy Path

Unhappy-path tests are mandatory.

Examples:

```text
Invalid input
Missing entity
Unauthorized operation
Business rule violation
Duplicate entity
Invalid state transition
Insufficient data
Repository failure
External service failure
AI validation failure
Database constraint violation
```

Each relevant failure should have an explicit test.

Do not rely exclusively on happy-path coverage.

---

# 22. Domain Tests

Domain tests must be framework independent.

A domain test must not require:

```text
Django
FastAPI
SQLAlchemy
Docker
PostgreSQL
HTTP
```

Example:

```python
def test_should_detect_anomaly_when_deviation_exceeds_threshold(): ...
```

The domain test should execute quickly.

---

# 23. Application Tests

Use Case tests should mock or fake external dependencies.

Example:

```text
Use Case
 ├── Fake Repository
 ├── Fake Unit of Work
 └── Fake External Service
```

The objective is to verify orchestration and application behavior.

---

# 24. Integration Tests

Integration tests verify interactions with real infrastructure.

Examples:

```text
PostgreSQL
SQLAlchemy
Alembic
Django ORM
External service
```

Use containers when appropriate.

Integration tests must not replace unit tests.

---

# 25. API Tests

API tests must verify:

- HTTP method;
- URL;
- authentication;
- request validation;
- response schema;
- status code;
- error response;
- business behavior.

Prefer testing through the public API boundary.

For FastAPI, use:

```text
TestClient
```

or an appropriate asynchronous HTTP test client.

---

# 26. Test Naming

Tests should describe behavior.

Prefer:

```text
test_should_create_measurement_when_input_is_valid
test_should_reject_measurement_when_contract_is_inactive
test_should_calculate_competency_gap
test_should_return_not_found_when_employee_does_not_exist
```

Avoid:

```text
test_create_1
test_service
test_model
```

---

# 27. Test Organization

A preferred structure is:

```text
tests/
├── unit/
│   ├── domain/
│   └── application/
│
├── integration/
│   ├── database/
│   └── infrastructure/
│
├── api/
│
├── e2e/
│
├── fixtures/
└── conftest.py
```

Project-specific organization is allowed if it improves bounded-context separation.

---

# 28. Test Doubles

Prefer, in order:

```text
Fake
Stub
Mock
```

Use mocks only when interaction verification is actually required.

Do not mock every dependency automatically.

The test should remain meaningful and close to the actual behavior.

---

# 29. Coverage

Coverage must be used as an indicator, not as the sole quality metric.

Do not write meaningless tests simply to increase coverage.

Critical business rules require explicit tests regardless of overall coverage percentage.

---

# 30. Static Analysis

The project uses:

```text
Ruff
Pyrefly
Pytest
```

Ruff is responsible for formatting and linting according to the project configuration.

Pyrefly must be used for static type checking.

Type hints are mandatory for application/domain code.

Avoid unnecessary:

```python
Any
# type: ignore
```

Every suppression must have a legitimate reason.

---

# 31. Code Formatting

Before committing, the formatter must be executed.

Preferred command:

```bash
uv run ruff format .
```

The actual command may be adjusted to the repository's configuration.

The agent must not manually format code when the formatter can perform the operation consistently.

---

# 32. Linting

Before committing:

```bash
uv run ruff check .
```

Fix all relevant errors before committing.

Do not disable lint rules merely to make CI pass.

If an exception is genuinely required, document the reason.

---

# 33. Type Checking

Before committing:

```bash
uv run pyrefly check
```

The exact target may be defined in project configuration.

New code must not introduce avoidable typing errors.

---

# 34. Tests Before Commit

Before every commit, run at minimum:

```bash
uv run pytest
uv run ruff format .
uv run ruff check .
uv run pyrefly check
```

The repository may define a `Makefile` that centralizes these commands.

If available, prefer the project's standard command.

Example:

```bash
make check
```

The agent must inspect the repository before inventing commands.

---

# 35. Git Flow

Repositories use Git Flow.

Respect the repository's existing Git Flow configuration and hooks.

Typical branches:

```text
main
develop
feature/*
release/*
hotfix/*
```

Do not commit directly to protected branches when the repository workflow forbids it.

Feature development should follow:

```text
develop
   ↓
feature/<name>
   ↓
tests
   ↓
validation
   ↓
commit
   ↓
pull request
   ↓
develop
```

---

# 36. Git Hooks

Git hooks are part of the development workflow.

The agent must not bypass hooks with:

```bash
git commit --no-verify
```

unless the user explicitly requests it for a specific reason.

Hooks should validate, whenever configured:

- formatting;
- linting;
- tests;
- type checking;
- commit message format.

---

# 37. Conventional Commits

All commits must follow Conventional Commits.

Examples:

```text
feat: add stock anomaly detection
fix: correct competency gap calculation
refactor: isolate contract allocation policy
test: add unhappy path for invalid measurement
docs: document anomaly API
chore: update project dependencies
perf: optimize cost center allocation query
build: update Docker image
ci: add test pipeline
```

The commit message must accurately describe the change.

Do not use vague messages such as:

```text
update
fixes
changes
stuff
work
```

---

# 38. Gitmoji

Commits must use Gitmoji together with Conventional Commits.

Examples:

```text
✨ feat: add stock anomaly detection
🐛 fix: correct competency gap calculation
♻️ refactor: isolate allocation policy
✅ test: add unhappy path for invalid measurement
📝 docs: document anomaly API
🔧 chore: update dependencies
⚡ perf: optimize cost center allocation query
🐳 build: update application container
💚 ci: add test pipeline
```

Use the Gitmoji that best represents the change.

Do not use Gitmoji merely for decoration.

---

# 39. Git Add and Commit

Before committing, inspect the working tree:

```bash
git status
```

Review the changes:

```bash
git diff
```

Stage explicitly:

```bash
git add <files>
```

Then create the commit:

```bash
git commit -m "✨ feat: add stock anomaly detection"
```

Do not blindly execute:

```bash
git add .
```

when unrelated changes may exist in the working tree.

---

# 40. Database Scripts and Stored Procedures

For projects involving large datasets, database-side processing is allowed when technically justified.

Allowed:

```text
Views
Stored Procedures
CTEs
Window Functions
Functions
Materialized Views
Indexes
Database-specific optimizations
```

However, database logic must have an explicit architectural boundary.

Python should access database-specific behavior through a repository or infrastructure adapter.

Example:

```text
Application
    ↓
Repository Interface
    ↓
Database Repository
    ↓
Stored Procedure / View
```

Do not expose SQL Server/PostgreSQL implementation details to the domain.

---

# 41. Contract Measurement and Cost Allocation

The project focuses on:

- contract measurement;
- financial allocation;
- cost centers;
- hierarchical cost centers;
- allocation rules;
- contracts;
- suppliers;
- measurement bulletins.

Domain concepts may include:

```text
Contract
Measurement
MeasurementBulletin
Supplier
CostCenter
AllocationRule
AllocationResult
```

The rateio/allocation rules must be represented as domain behavior or domain policies.

For example:

```text
Contract Value
      ↓
Allocation Policy
      ↓
Cost Center Hierarchy
      ↓
Allocation Entries
      ↓
Financial Result
```

Complex database calculations are acceptable when justified by volume or database capabilities.

The Python application must still expose them through well-defined infrastructure contracts.

---

# 42. Power BI Documentation

For projects that include Power BI:

The repository may contain:

```text
.pbix
```

when appropriate.

The README should document:

- data sources;
- data model;
- important measures;
- DAX logic;
- dashboard pages;
- business definitions;
- refresh requirements;
- screenshots;
- interaction examples;
- known limitations.

When requested, document:

```text
Dashboard screenshot
Dashboard interaction GIF
```

Do not commit unnecessarily large generated files unless repository policy permits them.

---

# 43. Docker

Docker is the standard infrastructure mechanism for reproducible local environments.

Typical services may include:

```text
application
database
nginx
```

Use Nginx when the architecture requires:

- reverse proxy;
- TLS termination;
- static file serving;
- routing;
- production-like deployment.

Do not introduce Nginx merely because it is available.

---

# 44. Docker Compose

Docker Compose should provide reproducible infrastructure.

Typical structure:

```text
services:
  app:
  db:
  nginx:
```

Use:

- health checks;
- named volumes;
- environment variables;
- isolated networks;
- explicit service dependencies.

`depends_on` must not be treated as proof that a database is ready.

Applications should handle database readiness appropriately.

---

# 45. Environment Configuration

Environment-specific configuration must not be hardcoded.

Typical files:

```text
.env.example
```

The repository must not commit:

```text
.env
```

when it contains secrets.

`.env.example` should document required variables without exposing credentials.

---

# 46. Documentation

Every significant feature must update documentation when necessary.

The README should explain:

- project purpose;
- architecture;
- prerequisites;
- local setup;
- environment variables;
- running the application;
- running tests;
- database migrations;
- Docker usage;
- API documentation;
- development workflow.

Architecture decisions should be documented when they are not obvious.

---

# 47. API Documentation

FastAPI/OpenAPI projects should expose API documentation through the framework.

The API contract should remain synchronized with implementation.

When OpenAPI is the source specification, changes to endpoints or schemas must update the specification first.

---

# 48. Error Handling

Errors must be intentional and meaningful.

Distinguish between:

```text
Domain Error
Application Error
Validation Error
Infrastructure Error
HTTP Error
```

Do not leak infrastructure exceptions directly to API consumers.

For example, avoid returning:

```text
SQLAlchemy IntegrityError
```

directly to clients.

Translate infrastructure errors into appropriate application/API errors.

---

# 49. Logging

Use structured and meaningful logging.

Do not log:

- passwords;
- tokens;
- secrets;
- credentials;
- unnecessary personal data.

Business-critical failures should contain enough contextual information for diagnosis without exposing sensitive information.

---

# 50. Security

The agent must consider:

- input validation;
- authentication;
- authorization;
- secret management;
- SQL injection;
- insecure deserialization;
- excessive data exposure;
- dependency vulnerabilities.

Never disable security mechanisms merely to simplify development unless explicitly restricted to a local development configuration.

---

# 51. Performance

Do not optimize prematurely.

When performance becomes relevant:

1. measure;
2. identify the bottleneck;
3. optimize;
4. add regression tests/benchmarks when appropriate;
5. document significant trade-offs.

Database optimization is preferred over unnecessary application-level data processing when the database is demonstrably better suited to the operation.

---

# 52. Refactoring

Refactoring must preserve behavior unless the task explicitly changes behavior.

Before refactoring:

```text
1. Understand current behavior
2. Check tests
3. Add missing tests if necessary
4. Refactor
5. Run complete validation
```

Avoid mixing unrelated refactoring with feature implementation.

---

# 53. Dependency Management

Use the repository's configured dependency manager.

For these projects, `uv` is preferred.

Do not automatically install `uv` or modify the developer's machine configuration.

Respect the existing lock file.

Do not upgrade dependencies without a reason.

---

# 54. Agent Behavior

Before modifying code, the AI agent must inspect:

```text
AGENTS.md
README.md
pyproject.toml
existing source tree
existing tests
Docker configuration
CI configuration
Git hooks
```

The agent must reuse existing conventions instead of creating parallel conventions.

Before creating a new abstraction, search for an existing abstraction that already solves the problem.

Before creating a new dependency, verify whether the project already provides equivalent functionality.

---

# 55. Do Not Break Existing Architecture

The agent must not solve a local problem by introducing architectural violations.

Examples of prohibited shortcuts:

```text
Controller → Database directly
View → Repository implementation directly
Domain → SQLAlchemy
Domain → Django
Domain → FastAPI
Use Case → HTTP request
Entity → external API
Streamlit → database
AI Agent → direct database manipulation
```

If an architectural exception is necessary, it must be explicitly justified.

---

# 56. Feature Development Checklist

Before considering a feature complete:

```text
[ ] Requirement understood
[ ] Existing architecture inspected
[ ] Specification updated if applicable
[ ] Domain rules identified
[ ] Use Case implemented
[ ] Infrastructure implemented
[ ] Presentation implemented
[ ] Happy path tested
[ ] Unhappy path tested
[ ] Boundary cases considered
[ ] Integration tests added when necessary
[ ] API contract updated
[ ] Documentation updated
[ ] Ruff format executed
[ ] Ruff lint executed
[ ] Pyrefly executed
[ ] Complete test suite executed
[ ] Git diff reviewed
[ ] Conventional Commit + Gitmoji prepared
```

---

# 57. Definition of Done

A feature is considered complete only when:

1. its behavior is specified;
2. business rules are located in the appropriate architectural layer;
3. happy paths are tested;
4. unhappy paths are tested;
5. relevant boundary conditions are tested;
6. infrastructure concerns are isolated;
7. type checking passes;
8. linting passes;
9. formatting passes;
10. tests pass;
11. documentation is updated when necessary;
12. the implementation respects SOLID and Clean Architecture;
13. no secrets are introduced;
14. the Git workflow is respected;
15. the commit follows Conventional Commits and Gitmoji.

---

# 58. Priority of Rules

When deciding how to implement a feature, use the following priority:

```text
1. Explicit user requirement
2. Project specification / acceptance criteria
3. Existing architectural constraints
4. Domain invariants
5. Existing repository conventions
6. This AGENTS.md
7. General implementation preferences
```

When requirements conflict, do not silently choose one.

Identify the conflict and ask for clarification when the decision could change business behavior or architecture.

---

# 59. Final Agent Rule

The agent must optimize for **correctness, maintainability, testability, and architectural consistency**, not merely for producing code that works in the shortest possible way.

A successful implementation is not simply:

```text
"It runs."
```

It must satisfy:

```text
It runs
+ It is specified
+ It is tested
+ It is typed
+ It is linted
+ It respects the architecture
+ It isolates business rules
+ It handles failure
+ It is maintainable
+ It is documented when necessary
```

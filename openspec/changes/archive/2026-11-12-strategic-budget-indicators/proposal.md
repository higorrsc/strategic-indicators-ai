# Proposal: Strategic Budget Indicators System

## Why

Organizations face significant challenges monitoring and controlling budget execution when contract expenses are distributed across multiple cost centers via complex allocation rules. Executive decision-making requires not only raw variance figures, but also actionable root-cause diagnostics, early detection of allocation anomalies or potential budgetary manipulation ("dumping"), and the ability to simulate future "what-if" scenarios before committing capital.

This project implements the Strategic Indicators System guided by **Spec-Driven Development (SDD)**, combining strict deterministic financial domain logic (DDD / Clean Architecture) with multi-provider executive AI intelligence (supporting local Ollama, Google Gemini, and OpenAI via Pydantic AI).

## What Changes

- Introduce the **Budgeting** bounded context (`budgeting`): hierarchical cost center management and budget target planning per period and expense category.
- Introduce the **Cost Allocation** bounded context (`cost-allocation`): contracts, suppliers, expense/measurement records, and flexible per-measurement cost allocation rules with strict 100% distribution and monetary rounding invariants.
- Introduce the **Budget Indicators & Simulation** bounded context (`budget-indicators`): deterministic calculation of Budget vs. Actual (variance amounts, execution rates, threshold alert statuses) and what-if forward scenario simulations.
- Introduce the **Strategic Intelligence** bounded context (`strategic-intelligence`): allocation anomaly detection heuristics (abrupt shifts, budget dumping) and an AI Port with a Pydantic AI adapter for executive summaries and scenario evaluations supporting interchangeable LLM providers (local Ollama, Google Gemini, OpenAI).
- Expose OpenAPI 3.1 contracts and BDD acceptance test specifications for all capabilities.

## Capabilities

### New Capabilities

- `budgeting`: Hierarchical cost centers and periodic budget planning per expense category.
- `cost-allocation`: Contracts, suppliers, financial measurements, and flexible cost allocation distribution across cost centers with strict monetary integrity.
- `budget-indicators`: Deterministic budget vs. actual calculation, burn-rate projections, and what-if scenario simulations.
- `strategic-intelligence`: Allocation anomaly detection and AI-powered executive insights and strategic recommendations with multi-provider LLM support (Ollama, Google, OpenAI).

### Modified Capabilities
<!-- Greenfield project: no pre-existing capabilities to modify. -->

## Impact

- **Architecture & Code**: Greenfield Clean Architecture structure in `src/` organized into cohesive bounded contexts following DDD.
- **APIs**: RESTful endpoints documented via OpenAPI for budgeting, measurements, allocations, indicators, what-if simulations, and AI insights.
- **Dependencies**: Ingestion of `fastapi`, `pydantic`, `pydantic-settings`, `pydantic-ai`, `pytest-bdd`, `httpx`, and related testing tooling into `pyproject.toml`.
- **Testing & Verification**: 100% isolated pure unit tests for domain invariants, contract tests, and BDD acceptance feature suites.

# strategic-intelligence Specification

## Purpose
Provides automated detection of cost allocation anomalies and generates executive-grade AI insights and scenario appraisals using interchangeable local and cloud LLM providers.

## Requirements

### Requirement: Allocation Anomaly and Fraud Detection

The system SHALL evaluate cost allocations against historical baselines and budget margins to detect suspicious patterns, sudden shifts, and budget dumping.

#### Scenario: Detect sudden allocation percentage spike

- **WHEN** a cost center with an average historical allocation share of 5% receives 45% of a major contract's allocation in a single measurement
- **THEN** the system flags the measurement with anomaly type "ABRUPT_ALLOCATION_SHIFT" and high risk severity

#### Scenario: Detect budget dumping between cost centers

- **WHEN** an allocation shifts expenses from an over-budget cost center to an under-budget cost center without corresponding operational rationale
- **THEN** the system flags the allocation entry with anomaly type "POTENTIAL_BUDGET_DUMPING"

### Requirement: AI Executive Summary and Root Cause Analysis

The system SHALL synthesize computed period indicators and detected anomalies into structured executive insights using configured AI providers.

#### Scenario: Generate executive period insight report

- **WHEN** a user requests an executive summary for period "2026-03"
- **THEN** the system invokes the AI Port and returns a validated schema containing executive summary, top cost driver root causes, and strategic recommendations

#### Scenario: Fallback behavior on AI provider unavailability

- **WHEN** the configured external or local LLM service fails or times out
- **THEN** the system returns the deterministic indicators alongside an error indicator, without crashing financial data delivery

### Requirement: Multi-Provider LLM Configuration

The system SHALL support configuring interchangeable AI backends including local Ollama instances, Google Gemini, and OpenAI via environment settings.

#### Scenario: Local inference execution via Ollama

- **WHEN** the system is configured with AI_PROVIDER="ollama" and a valid Ollama base URL
- **THEN** requests routed to the AI Port execute against the local Ollama instance without transmitting data to external third-party cloud services

#### Scenario: Cloud inference execution via Google or OpenAI

- **WHEN** the system is configured with AI_PROVIDER="google" or "openai" and corresponding credentials
- **THEN** requests routed to the AI Port authenticate and execute against the selected cloud LLM provider using structured output validation

### Requirement: Downloadable PDF Executive Briefing Report

The system SHALL provide an HTTP endpoint to download a styled binary PDF document synthesizing period indicators, AI executive narrative, identified anomalies, and strategic recommendations.

#### Scenario: Successfully download PDF executive summary for valid period

- **WHEN** a client sends a GET request to `/api/v1/intelligence/executive-summary/pdf` with query parameter `period=2026-03`
- **THEN** the system returns HTTP 200 with `Content-Type: application/pdf`, `Content-Disposition: attachment; filename="executive-summary-2026-03.pdf"`, and valid binary PDF content containing financial KPIs, executive narrative, anomalies table, and recommendations

#### Scenario: Reject invalid period format for PDF download

- **WHEN** a client sends a GET request to `/api/v1/intelligence/executive-summary/pdf` with invalid period `2026-13` or `invalid`
- **THEN** the system returns HTTP 422 Unprocessable Entity describing the invalid period format

#### Scenario: Fallback rendering when AI provider is unavailable

- **WHEN** the configured external or local AI model fails or times out during PDF report generation
- **THEN** the system still produces and streams the PDF document using deterministic fallback indicators and an explicit offline advisory banner rather than failing the request

### Requirement: Multilingual AI Executive Analysis

The system SHALL generate executive insights, root causes, and strategic recommendations in the user's requested language (`pt-br` or `en-us`).

#### Scenario: Generate executive summary in Brazilian Portuguese

- **WHEN** a client sends a GET request to `/api/v1/intelligence/executive-summary?period=2026-03&lang=pt-br`
- **THEN** the system generates the executive analysis, root causes, and recommendations in Brazilian Portuguese

#### Scenario: Generate executive summary in English

- **WHEN** a client sends a GET request to `/api/v1/intelligence/executive-summary?period=2026-03&lang=en-us`
- **THEN** the system generates the executive analysis, root causes, and recommendations in American English

#### Scenario: Default language when lang parameter is omitted

- **WHEN** a client sends a GET request to `/api/v1/intelligence/executive-summary?period=2026-03` without specifying `lang`
- **THEN** the system defaults to `pt-br`

#### Scenario: Reject unsupported language parameter

- **WHEN** a client requests an executive summary with `lang=fr-fr` or `lang=es-es`
- **THEN** the system rejects the request with HTTP 422 Unprocessable Entity

#### Scenario: Localized deterministic fallback when AI is unavailable

- **WHEN** the AI provider fails and `lang=en-us` was requested
- **THEN** the system returns deterministic summary text and advisory message written in English

### Requirement: Multilingual PDF Executive Report

The system SHALL generate downloadable PDF executive briefing reports with all titles, labels, badges, and tables localized according to the specified language parameter.

#### Scenario: Download PDF report in Portuguese

- **WHEN** a client requests `/api/v1/intelligence/executive-summary/pdf?period=2026-03&lang=pt-br`
- **THEN** the system streams a binary PDF with Brazilian Portuguese headers (e.g., "Sumário Executivo", "Orçamento Planejado", "Variação") and Portuguese narrative

#### Scenario: Download PDF report in English

- **WHEN** a client requests `/api/v1/intelligence/executive-summary/pdf?period=2026-03&lang=en-us`
- **THEN** the system streams a binary PDF with English headers (e.g., "Executive Briefing", "Planned Budget", "Variance") and English narrative

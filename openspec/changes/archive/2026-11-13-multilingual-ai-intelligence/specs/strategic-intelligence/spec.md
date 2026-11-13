# strategic-intelligence Specification Delta: Multilingual AI Intelligence

## Purpose

Enables requesting AI-generated executive summaries and downloadable PDF briefing documents in specific languages (`pt-br` and `en-us`).

## ADDED Requirements

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

# Spec Delta: Strategic Intelligence

## Purpose

Provides automated detection of cost allocation anomalies and generates executive-grade AI insights and scenario appraisals using interchangeable local and cloud LLM providers.

## ADDED Requirements

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

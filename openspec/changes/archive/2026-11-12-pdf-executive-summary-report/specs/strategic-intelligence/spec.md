# Spec Delta: strategic-intelligence

## ADDED Requirements

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

# Proposal: PDF Executive Summary Report

## Why

Stakeholders and executive leaders require human-readable, professional briefing documents that can be easily shared via email, downloaded for offline review, or presented in executive meetings. Currently, the `GET /api/v1/intelligence/executive-summary` endpoint returns raw JSON, which is optimal for machine-to-machine integration and dashboard consumption, but awkward for direct human distribution. Introducing a dedicated endpoint that renders the synthesized AI analysis and financial indicators directly into a formatted PDF document provides immediate reporting flexibility without modifying the existing JSON contract.

## What Changes

- Add a new endpoint `GET /api/v1/intelligence/executive-summary/pdf` that generates and streams a styled, publication-ready PDF report for a requested fiscal period.
- Preserve the existing `GET /api/v1/intelligence/executive-summary` JSON endpoint unchanged for API integrations.
- Introduce a PDF report generation service utilizing `fpdf2` (pure Python, zero native system dependencies) to format executive summary text, root causes, strategic action recommendations, financial health badge, indicators summary table, and identified allocation anomalies.
- Configure proper HTTP response headers (`Content-Type: application/pdf` and `Content-Disposition: attachment; filename="executive-summary-{period}.pdf"`).
- Add `fpdf2` to project production dependencies.

## Capabilities

### New Capabilities
<!-- None: this change extends the existing strategic-intelligence capability -->

### Modified Capabilities

- `strategic-intelligence`: Add requirement for generating formatted binary PDF executive briefing reports containing financial indicators, AI executive synthesis, anomaly tables, and action plans.

## Impact

- **API**: New endpoint `GET /api/v1/intelligence/executive-summary/pdf?period=YYYY-MM`.
- **Dependencies**: Addition of `fpdf2` in `pyproject.toml`.
- **Presentation & Infrastructure**: New PDF generation service/adapter implementing layout, typography, tables, and colors.
- **Backwards Compatibility**: Fully backwards compatible; existing JSON endpoint remains unchanged.

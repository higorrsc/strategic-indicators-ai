# Design: PDF Executive Summary Report

## Context

The application provides financial governance, cost allocation, budget variance indicators, and strategic intelligence powered by Pydantic AI. The existing endpoint `GET /api/v1/intelligence/executive-summary` generates an `ExecutiveSummaryDTO` containing:

- Financial health status (`NORMAL`, `WARNING`, `CRITICAL_OVERRUN`)
- AI-synthesized narrative summary
- Root causes and strategic recommendations
- Period indicators summary (budgeted vs. actual amounts per cost center)
- Detected allocation anomalies (abrupt shifts, budget dumping)

Currently, this information is only accessible via JSON. Executive stakeholders need a clean, styled, ready-to-print or attachable PDF file.

## Goals / Non-Goals

**Goals:**

- Provide a dedicated endpoint `GET /api/v1/intelligence/executive-summary/pdf?period=YYYY-MM`.
- Generate visually appealing, branded, multi-section executive reports in binary PDF format.
- Maintain Clean Architecture: keep the domain and application use cases independent of PDF rendering libraries.
- Use a pure-Python, zero-native-C-dependency library (`fpdf2`) that runs seamlessly inside Docker Python 3.15-slim containers without requiring heavy system dependencies (like Cairo or Pango).
- Ensure graceful fallback: if AI generation fails, render the report with deterministic calculations and an offline advisory banner.

**Non-Goals:**

- Modifying or breaking the existing `GET /api/v1/intelligence/executive-summary` JSON endpoint.
- Interactive form filling or PDF editing; this is strictly an outbound document generation pipeline.
- HTML-to-PDF rendering through headless Chromium or WeasyPrint (unnecessary complexity and Docker image bloat).

## Decisions

### Decision 1: Use `fpdf2` for PDF Generation

- **Rationale**: `fpdf2` is a mature, actively maintained, pure-Python library with built-in table layout (`pdf.table()`), cell borders, headers/footers with dynamic page counts, and zero native system library prerequisites.
- **Alternatives Considered**:
  - `weasyprint`: Excellent CSS support, but requires Cairo, Pango, and GDK system packages which complicate minimal Docker container builds.
  - `reportlab`: Powerful but complex low-level API with legacy baggage and proprietary extensions.
  - `pdfkit` / `wkhtmltopdf`: Relies on deprecated external binaries and security vulnerabilities.

### Decision 2: Place PDF Generator in Presentation Layer (`src/presentation/reports/`)

- **Rationale**: In Clean Architecture, translating application DTOs into specific client-facing presentation media (HTML, JSON, CSV, PDF) is a presentation adapter responsibility. The application use case (`GenerateExecutiveSummaryUseCase`) already returns the complete `ExecutiveSummaryDTO`.
- **Alternatives Considered**:
  - Creating a domain or application port for PDF generation: Adds unnecessary abstraction layers when the PDF is strictly an alternate HTTP presentation format of an already-existing use case.

### Decision 3: Document Layout Structure

1. **Header**: Title banner with corporate branding, target fiscal period, and color-coded status badge (`NORMAL` in green, `WARNING` in amber, `CRITICAL_OVERRUN` in crimson).
2. **Executive Narrative**: Formatted executive summary paragraphs and financial health evaluation.
3. **Key Root Causes & Strategic Recommendations**: Visual callout cards with actionable bullet points.
4. **Indicators Summary Table**: Tabular breakdown of each cost center (Budgeted, Actual, Variance, Execution Rate %, Status).
5. **Allocation Anomalies Table**: Detailed list of flagged anomalies (severity, type, description).
6. **Footer**: Generation timestamp and dynamic page numbering ("Page X of Y").

## Risks / Trade-offs

- **[Risk] Large narrative text overflowing page boundaries** → **Mitigation**: `fpdf2` automatically handles multi-page flow and page breaks with persistent headers and footers.
- **[Risk] High memory usage during concurrent downloads** → **Mitigation**: Streaming generated PDF bytes directly as response memory buffer without writing intermediate files to disk.
- **[Risk] AI timeout during report generation** → **Mitigation**: The underlying use case already contains autonomous fallback mechanisms to return deterministic summaries and advisory notices if LLM providers time out.

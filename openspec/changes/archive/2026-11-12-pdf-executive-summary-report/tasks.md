# Tasks: PDF Executive Summary Report

## 1. Dependency and Scaffolding

- [x] 1.1 Add `fpdf2` dependency to `pyproject.toml` and synchronize environment with `uv sync`
- [x] 1.2 Create `src/presentation/reports/executive_summary_pdf.py` defining `ExecutiveSummaryPDFBuilder` and verify module imports

## 2. PDF Report Generator Implementation

- [x] 2.1 Implement document layout, header styling, financial health badge, and footer with dynamic page counts in `ExecutiveSummaryPDFBuilder`
- [x] 2.2 Implement executive narrative, root causes, and strategic recommendations sections with structured typography
- [x] 2.3 Implement tabular formatting for cost center indicators and allocation anomalies
- [x] 2.4 Add unit tests in `tests/unit/presentation/test_executive_summary_pdf.py` verifying PDF binary generation, table rendering, and fallback behavior

## 3. Router Integration and Verification

- [x] 3.1 Register `GET /api/v1/intelligence/executive-summary/pdf` endpoint in `src/presentation/api/v1/intelligence_router.py` returning binary PDF response and attachment header
- [x] 3.2 Add API integration tests in `tests/api/test_api_indicators_and_intelligence.py` validating HTTP 200, `application/pdf` media type, `Content-Disposition` header, and 422 for invalid period format
- [x] 3.3 Run full quality assurance suite (`uv run ruff check .`, `uv run ruff format --check .`, `uv run pyrefly check`, `uv run pytest`) and rebuild application container

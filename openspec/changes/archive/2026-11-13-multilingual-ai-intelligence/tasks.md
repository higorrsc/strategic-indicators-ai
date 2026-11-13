# Tasks: Multilingual AI Executive Intelligence (PT-BR and EN-US)

- [x] 1. Domain Types & Contracts
  - [x] 1.1 Define `SupportedLanguage` enum in `src/shared/domain/value_objects/language.py`
  - [x] 1.2 Update `AIPort` signature in `src/intelligence/application/ports/ai_port.py` to accept `language: SupportedLanguage`
  - [x] 1.3 Add `language` field to `ExecutiveSummaryDTO` in `src/intelligence/application/dto.py`

- [x] 2. AI Provider Adapters & Localized Fallback
  - [x] 2.1 Update Pydantic AI prompts in `src/intelligence/infrastructure/pydantic_ai_adapter.py` with language instructions
  - [x] 2.2 Implement localized deterministic fallback templates for `pt-br` and `en-us` in `GenerateExecutiveSummaryUseCase`
  - [x] 2.3 Write unit tests in `tests/unit/intelligence/test_intelligence.py` verifying prompt customization and fallback localization

- [x] 3. PDF Generator Localization
  - [x] 3.1 Implement `I18N_LABELS` catalog in `src/presentation/reports/executive_summary_pdf.py`
  - [x] 3.2 Update `ExecutiveSummaryPDFBuilder` to use localized labels, headers, badges, and advisory notices based on `dto.language`
  - [x] 3.3 Write unit tests in `tests/unit/presentation/test_executive_summary_pdf.py` verifying PDF rendering for both `pt-br` and `en-us`

- [x] 4. Presentation & API Layer
  - [x] 4.1 Update `GenerateExecutiveSummaryUseCase` to accept `language: SupportedLanguage`
  - [x] 4.2 Update `GET /api/v1/intelligence/executive-summary` to accept `lang: SupportedLanguage = Query(default=SupportedLanguage.PT_BR)`
  - [x] 4.3 Update `GET /api/v1/intelligence/executive-summary/pdf` to accept `lang: SupportedLanguage = Query(default=SupportedLanguage.PT_BR)` and adjust filename
  - [x] 4.4 Write API tests in `tests/api/test_api_indicators_and_intelligence.py` verifying both endpoints with `lang=pt-br`, `lang=en-us`, and invalid `lang` (422)

- [x] 5. Documentation & Verification
  - [x] 5.1 Run full quality suite (`uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`)
  - [x] 5.2 Update `README.md` and OpenAPI documentation

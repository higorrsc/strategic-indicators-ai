# Proposal: Multilingual AI Executive Intelligence (PT-BR and EN-US)

## Summary

Add native multilingual support to the Strategic Intelligence layer, allowing AI-generated executive summaries, root cause analyses, strategic recommendations, and downloadable PDF briefing reports to be requested in either Brazilian Portuguese (`pt-br`) or American English (`en-us`).

## Motivation & Problem Statement

Currently, the LLM prompts and deterministic fallback outputs are defined with fixed Portuguese/English mixed strings or single-language defaults. In global and bilingual corporate environments, executives, board members, and regional controllers need briefing reports in their preferred operating language.
Specifically:

1. The AI narrative, root causes, and strategic recommendations should be generated natively in the chosen language.
2. If the LLM provider fails or is offline, the deterministic fallback message and advisory notices must also respect the requested language.
3. The downloadable binary PDF executive briefing document must dynamically render all visual headers, KPI labels, badges, and table columns in the selected language (`pt-br` or `en-us`).

## Proposed Changes

1. **Locale Domain Definition:**
   - Define a supported language enum/value object `LanguageLocale` (`pt-br`, `en-us`) with default `pt-br`.
2. **AI Provider Prompts:**
   - Parameterize Pydantic AI prompt definitions with explicit instructions enforcing output in the requested language.
   - Maintain structured output schema compliance (`executive_summary`, `root_causes`, `strategic_recommendations`) regardless of language.
3. **Deterministic Fallback Localization:**
   - Provide localized templates for deterministic summaries when AI is disabled or unreachable.
4. **PDF Generator Localization:**
   - Add a localization dictionary / i18n bundle for `ExecutiveSummaryPDFBuilder` covering document titles, KPI card labels, status badges (`CRITICAL_OVERRUN` -> `ESTOURO CRÍTICO` / `CRITICAL OVERRUN`), table headers, and advisory banners.
5. **API & Presentation:**
   - Add query parameter `lang` (values: `pt-br`, `en-us`, default: `pt-br`) to:
     - `GET /api/v1/intelligence/executive-summary?period=YYYY-MM&lang=pt-br`
     - `GET /api/v1/intelligence/executive-summary/pdf?period=YYYY-MM&lang=pt-br`
   - Validate and reject unsupported locales with HTTP 422.

## Out of Scope

- Dynamic translation of user-entered contract titles or cost center descriptions (only system-generated narratives, labels, and summaries are localized).
- Additional languages beyond `pt-br` and `en-us`.

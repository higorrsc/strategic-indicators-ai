# Design: Multilingual AI Executive Intelligence (PT-BR and EN-US)

## Architectural Flow

```text
Presentation Layer:
  GET /api/v1/intelligence/executive-summary?period=YYYY-MM&lang=pt-br|en-us
  GET /api/v1/intelligence/executive-summary/pdf?period=YYYY-MM&lang=pt-br|en-us
       ↓
Application Layer:
  GenerateExecutiveSummaryUseCase(period: Period, language: SupportedLanguage = SupportedLanguage.PT_BR)
       ↓
Domain Layer:
  Enum: SupportedLanguage("pt-br", "en-us")
  Port: AIExecutivePort.generate_executive_summary(..., language: SupportedLanguage)
       ↑
Infrastructure Layer:
  PydanticAIEngine:
    - Injects language constraint into system prompt & user prompt
    - Localized FallbackEngine for offline LLM mode
  PDF Builder:
    - I18N dictionary for UI labels, badges, and headers
```

## Domain Design

1. **Value Object / Enum: `SupportedLanguage`**

   ```python
   class SupportedLanguage(str, Enum):
       PT_BR = "pt-br"
       EN_US = "en-us"
   ```

2. **AI Port Contract:**

   ```python
   class AIExecutivePort(Protocol):
       async def generate_executive_summary(
           self,
           indicators: PeriodIndicatorsDTO,
           anomalies: list[AnomalyDTO],
           language: SupportedLanguage = SupportedLanguage.PT_BR,
       ) -> ExecutiveSummaryDTO: ...
   ```

3. **ExecutiveSummaryDTO:**
   - Add field `language: SupportedLanguage = SupportedLanguage.PT_BR`.

## Prompt Engineering & Adapters

1. **Pydantic AI Prompt Formulation:**
   - When `language == SupportedLanguage.PT_BR`:
     - System prompt specifies: *"Você é um Diretor Financeiro (CFO) e Especialista em Governança Orçamentária. Responda estritamente em Português do Brasil (pt-br)."*
   - When `language == SupportedLanguage.EN_US`:
     - System prompt specifies: *"You are an executive CFO and Corporate Budget Governance Specialist. Answer strictly in American English (en-us)."*
2. **Deterministic Fallback Engine:**
   - Dictionary mapping `SupportedLanguage` to localized fallback text for `executive_summary`, `root_causes`, `strategic_recommendations`, and advisory notices.

## PDF Report Generator (`ExecutiveSummaryPDFBuilder`)

1. Create `I18N_LABELS` catalog:

   ```python
   I18N = {
       SupportedLanguage.PT_BR: {
           "report_title": "RELATÓRIO ESTRATÉGICO & INTELIGÊNCIA FINANCEIRA",
           "executive_summary": "Visão Geral Executiva",
           "budget_planned": "Orçado Planejado",
           "budget_actual": "Realizado Aprovado",
           "budget_variance": "Variação Orçamentária",
           "status_critical": "ESTOURO CRÍTICO",
           "status_warning": "ATENÇÃO",
           "status_healthy": "ECONOMIA SAUDÁVEL",
           "status_neutral": "NEUTRO",
           "indicators_table": "Detalhamento por Centro de Custo",
           "col_code": "Código",
           "col_budget": "Orçado",
           "col_spent": "Realizado",
           "col_variance": "Variação",
           "col_pct": "Consumo",
           "col_status": "Status",
           "anomalies_title": "Auditoria de Anomalias & Fraudes",
           "recommendations_title": "Plano de Ação Estratégico",
           "fallback_warning": "AVISO: Análise determinística offline. Serviço de IA indisponível.",
       },
       SupportedLanguage.EN_US: {
           "report_title": "STRATEGIC REPORT & FINANCIAL INTELLIGENCE",
           "executive_summary": "Executive Overview",
           "budget_planned": "Planned Budget",
           "budget_actual": "Approved Actuals",
           "budget_variance": "Budget Variance",
           "status_critical": "CRITICAL OVERRUN",
           "status_warning": "WARNING",
           "status_healthy": "HEALTHY SAVINGS",
           "status_neutral": "NEUTRAL",
           "indicators_table": "Cost Center Breakdown",
           "col_code": "Code",
           "col_budget": "Planned",
           "col_spent": "Actual",
           "col_variance": "Variance",
           "col_pct": "Exec %",
           "col_status": "Status",
           "anomalies_title": "Anomaly & Audit Diagnostics",
           "recommendations_title": "Strategic Action Plan",
           "fallback_warning": "NOTICE: Deterministic offline mode. External AI service unavailable.",
       },
   }
   ```

2. Pass `language: SupportedLanguage` to `ExecutiveSummaryPDFBuilder.build(dto, language=dto.language)`.

## API Specification

- Query parameter: `lang: SupportedLanguage = Query(default=SupportedLanguage.PT_BR, description="Language for generated intelligence: pt-br or en-us")`.
- `Content-Disposition` filename adjusted:
  - Portuguese: `sumario-executivo-2026-03-pt-br.pdf`
  - English: `executive-summary-2026-03-en-us.pdf`

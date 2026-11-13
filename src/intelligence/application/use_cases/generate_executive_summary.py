"""Use case generating executive summary and strategic insights for a period."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from src.indicators.application.dto import ComputePeriodIndicatorsQuery
from src.indicators.application.use_cases import ComputePeriodIndicatorsUseCase
from src.indicators.domain.models import CostCenterIndicator, IndicatorStatus
from src.intelligence.application.dto import AnomalyDTO, ExecutiveSummaryDTO
from src.intelligence.application.ports.ai_analysis_cache_repository import (
    AIAnalysisCacheRepository,
)
from src.intelligence.application.ports.ai_port import AIPort
from src.intelligence.application.services.data_fingerprint_service import (
    compute_intelligence_data_hash,
)
from src.intelligence.application.use_cases.analyze_allocation_anomalies import (
    AnalyzeAllocationAnomaliesUseCase,
)
from src.intelligence.domain.cache import AIAnalysisCache, CacheStatus
from src.intelligence.domain.exceptions import AIProviderError
from src.intelligence.domain.models import (
    AnomalySeverity,
    AnomalyType,
)
from src.shared.config.settings import Settings, get_settings
from src.shared.domain.value_objects import (
    Money,
    Percentage,
    Period,
    SupportedLanguage,
)


class GenerateExecutiveSummaryUseCase:
    """Coordinates deterministic indicator calculation, anomaly detection, and AI."""

    def __init__(
        self,
        indicators_use_case: ComputePeriodIndicatorsUseCase,
        anomalies_use_case: AnalyzeAllocationAnomaliesUseCase,
        ai_port: AIPort,
        cache_repository: AIAnalysisCacheRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize use case with indicators, anomaly detector, AI port, and cache.

        Args:
            indicators_use_case: Use case computing planned vs actual variance.
            anomalies_use_case: Use case detecting allocation anomalies.
            ai_port: Application port for AI model interactions.
            cache_repository: Optional repository for AI analysis caching.
            settings: Application configuration settings.
        """
        self._indicators_use_case = indicators_use_case
        self._anomalies_use_case = anomalies_use_case
        self._ai_port = ai_port
        self._cache_repo = cache_repository
        self._settings = settings or get_settings()

    async def execute(
        self,
        period: Period,
        language: SupportedLanguage = SupportedLanguage.PT_BR,
        cost_center_id: UUID | None = None,
        accounting_account_id: UUID | None = None,
        force_refresh: bool = False,
    ) -> ExecutiveSummaryDTO:
        """Generate comprehensive executive report with caching and scoping.

        Args:
            period: Target fiscal period.
            language: Desired language locale (default: pt-br).
            cost_center_id: Optional scope cost center UUID.
            accounting_account_id: Optional scope accounting account UUID.
            force_refresh: Force LLM recalculation bypassing valid cache.

        Returns:
            ExecutiveSummaryDTO: Consolidated report with deterministic and AI insights.
        """
        indicators_summary = await self._indicators_use_case.execute(
            ComputePeriodIndicatorsQuery(
                period=str(period), cost_center_id=cost_center_id
            )
        )
        domain_indicators = [
            CostCenterIndicator(
                cost_center_id=ind.cost_center_id,
                cost_center_code=ind.cost_center_code,
                period=period,
                budgeted_amount=Money(ind.budgeted_amount, ind.currency),
                actual_amount=Money(ind.actual_amount, ind.currency),
                variance_amount=Money(ind.variance_amount, ind.currency),
                execution_rate=Percentage.from_number(ind.execution_rate),
                status=IndicatorStatus(ind.status),
            )
            for ind in indicators_summary.indicators
        ]

        all_anomalies = await self._anomalies_use_case.analyze_period(period)
        if cost_center_id:
            domain_anomalies = [
                a for a in all_anomalies if a.cost_center_id == cost_center_id
            ]
        else:
            domain_anomalies = all_anomalies

        anomaly_dtos = [AnomalyDTO.from_domain(a) for a in domain_anomalies]

        current_data_hash = compute_intelligence_data_hash(
            period=period,
            language=language,
            cost_center_id=cost_center_id,
            accounting_account_id=accounting_account_id,
            indicators=indicators_summary.indicators,
            anomalies=[
                {
                    "measurement_id": str(a.measurement_id),
                    "contract_id": str(a.contract_id),
                    "cost_center_id": str(a.cost_center_id),
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "description": a.description,
                }
                for a in domain_anomalies
            ],
        )

        cache_key = (
            f"summary:p={period}:l={language.value}:"
            f"cc={cost_center_id or 'all'}:acc={accounting_account_id or 'all'}"
        )

        cached_entry = (
            await self._cache_repo.get_by_key(cache_key) if self._cache_repo else None
        )
        now = datetime.now(UTC)

        if cached_entry is None:
            status = CacheStatus.FORCED_REFRESH if force_refresh else CacheStatus.MISS
        else:
            status = cached_entry.evaluate_status(
                current_data_hash, force_refresh=force_refresh, now=now
            )

        if status == CacheStatus.HIT and cached_entry is not None:
            payload = cached_entry.summary_payload
            cached_anomalies = [
                AnomalyDTO(
                    measurement_id=UUID(a["measurement_id"]),
                    contract_id=UUID(a["contract_id"]),
                    cost_center_id=UUID(a["cost_center_id"]),
                    anomaly_type=AnomalyType(a["anomaly_type"]),
                    severity=AnomalySeverity(a["severity"]),
                    description=a["description"],
                    baseline_percentage=a.get("baseline_percentage"),
                    actual_percentage=a.get("actual_percentage"),
                )
                for a in payload.get("anomalies", [])
            ]
            return ExecutiveSummaryDTO(
                period=period,
                financial_health_status=payload["financial_health_status"],
                executive_summary=payload["executive_summary"],
                root_causes=payload["root_causes"],
                strategic_recommendations=payload["strategic_recommendations"],
                anomalies=cached_anomalies,
                indicators_summary=indicators_summary,
                is_fallback=payload.get("is_fallback", False),
                ai_provider=payload.get("ai_provider", self._settings.AI_PROVIDER),
                language=language,
                cache_status=CacheStatus.HIT,
                is_cached=True,
                cached_at=cached_entry.created_at,
            )

        try:
            ai_response = await self._ai_port.generate_executive_summary(
                indicators=domain_indicators,
                anomalies=domain_anomalies,
                period=period,
                language=language,
            )
            result_dto = ExecutiveSummaryDTO(
                period=period,
                financial_health_status=ai_response.financial_health_status,
                executive_summary=ai_response.executive_summary,
                root_causes=ai_response.root_causes,
                strategic_recommendations=ai_response.strategic_recommendations,
                anomalies=anomaly_dtos,
                indicators_summary=indicators_summary,
                is_fallback=False,
                ai_provider=self._settings.AI_PROVIDER,
                language=language,
                cache_status=status,
                is_cached=False,
                cached_at=None,
            )
        except AIProviderError as err:
            logging.getLogger(__name__).warning(
                "AI provider failed, falling back: %s", err
            )
            overruns = [
                i
                for i in indicators_summary.indicators
                if i.status != IndicatorStatus.NORMAL.value
            ]

            if language == SupportedLanguage.PT_BR:
                root_causes = [
                    f"Centro de custo {i.cost_center_code} excedeu o limite: "
                    f"taxa de execução {i.execution_rate}%."
                    for i in overruns
                ]
                if domain_anomalies:
                    root_causes.extend(
                        f"{a.anomaly_type.value}: {a.description}"
                        for a in domain_anomalies
                    )
                if not root_causes:
                    root_causes.append(
                        "Todos os centros de custo operaram dentro dos limites "
                        "orçamentários."
                    )

                summary_text = (
                    f"Relatório executivo para o período {period} gerado via "
                    f"fallback determinístico.\n"
                    f"Planejado: {indicators_summary.total_budgeted}, "
                    f"Realizado: {indicators_summary.total_actual}, "
                    f"Variação: {indicators_summary.total_variance}."
                )
                recommendations = [
                    "Realizar auditoria operacional nos centros de custo "
                    "com estouro orçamentário.",
                    "Revisar desvios de alocação de custos sinalizados.",
                ]
                health_status = "INDISPONÍVEL (FALLBACK DE IA)"
            else:
                root_causes = [
                    f"Cost center {i.cost_center_code} exceeded threshold: "
                    f"execution rate {i.execution_rate}%."
                    for i in overruns
                ]
                if domain_anomalies:
                    root_causes.extend(
                        f"{a.anomaly_type.value}: {a.description}"
                        for a in domain_anomalies
                    )
                if not root_causes:
                    root_causes.append(
                        "All cost centers operated within budget limits."
                    )

                summary_text = (
                    f"Executive report for period {period} generated via "
                    f"deterministic fallback.\n"
                    f"Planned: {indicators_summary.total_budgeted}, "
                    f"Actual: {indicators_summary.total_actual}, "
                    f"Variance: {indicators_summary.total_variance}."
                )
                recommendations = [
                    "Conduct operational audit of over-budget cost centers.",
                    "Review flagged cost allocation shifts.",
                ]
                health_status = "UNAVAILABLE (AI FALLBACK)"

            result_dto = ExecutiveSummaryDTO(
                period=period,
                financial_health_status=health_status,
                executive_summary=summary_text,
                root_causes=root_causes,
                strategic_recommendations=recommendations,
                anomalies=anomaly_dtos,
                indicators_summary=indicators_summary,
                is_fallback=True,
                ai_provider=self._settings.AI_PROVIDER,
                language=language,
                cache_status=status,
                is_cached=False,
                cached_at=None,
            )

        if self._cache_repo and not result_dto.is_fallback:
            ttl_hours = getattr(self._settings, "AI_CACHE_TTL_HOURS", 24)
            payload_to_store = {
                "financial_health_status": result_dto.financial_health_status,
                "executive_summary": result_dto.executive_summary,
                "root_causes": result_dto.root_causes,
                "strategic_recommendations": result_dto.strategic_recommendations,
                "anomalies": [
                    {
                        "measurement_id": str(a.measurement_id),
                        "contract_id": str(a.contract_id),
                        "cost_center_id": str(a.cost_center_id),
                        "anomaly_type": a.anomaly_type.value,
                        "severity": a.severity.value,
                        "description": a.description,
                        "baseline_percentage": a.baseline_percentage,
                        "actual_percentage": a.actual_percentage,
                    }
                    for a in result_dto.anomalies
                ],
                "is_fallback": result_dto.is_fallback,
                "ai_provider": result_dto.ai_provider,
            }

            if cached_entry is not None:
                cached_entry.renew(
                    current_data_hash=current_data_hash,
                    new_payload=payload_to_store,
                    ttl_hours=ttl_hours,
                    now=now,
                )
                await self._cache_repo.save(cached_entry)
            else:
                new_cache = AIAnalysisCache(
                    id=uuid4(),
                    cache_key=cache_key,
                    period=period,
                    language=language,
                    cost_center_id=cost_center_id,
                    accounting_account_id=accounting_account_id,
                    data_hash=current_data_hash,
                    summary_payload=payload_to_store,
                    created_at=now,
                    expires_at=now + timedelta(hours=ttl_hours),
                    updated_at=now,
                )
                await self._cache_repo.save(new_cache)

        return result_dto

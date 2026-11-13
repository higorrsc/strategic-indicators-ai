"""Strategic intelligence dependency providers and type annotations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.indicators.application.use_cases.queries import (
    ComputePeriodIndicatorsUseCase,
)
from src.intelligence.application.ports.ai_analysis_cache_repository import (
    AIAnalysisCacheRepository,
)
from src.intelligence.application.ports.ai_port import AIPort
from src.intelligence.application.use_cases.queries import (
    AnalyzeAllocationAnomaliesUseCase,
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.infrastructure.repositories import (
    SqlAlchemyAIAnalysisCacheRepository,
)

from .allocation import get_measurement_repository
from .container import DependencyContainer, get_container
from .database import get_db_session
from .indicators import get_compute_period_indicators_use_case


def get_ai_analysis_cache_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> AIAnalysisCacheRepository:
    """Provide AI analysis cache repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        AIAnalysisCacheRepository: AI analysis cache repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyAIAnalysisCacheRepository(session)
    return container.ai_cache_repo


def get_ai_port(
    container: Annotated[DependencyContainer, Depends(get_container)],
) -> AIPort:
    """Provide AI application port adapter.

    Args:
        container: Dependency container.

    Returns:
        AIPort: AI adapter.
    """
    return container.ai_port


def get_analyze_anomalies_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
    indicators_uc: Annotated[
        ComputePeriodIndicatorsUseCase,
        Depends(get_compute_period_indicators_use_case),
    ],
) -> AnalyzeAllocationAnomaliesUseCase:
    """Provide AnalyzeAllocationAnomaliesUseCase.

    Args:
        measurement_repo: Measurement repository.
        indicators_uc: Period indicators use case.

    Returns:
        AnalyzeAllocationAnomaliesUseCase: Instantiated use case.
    """
    return AnalyzeAllocationAnomaliesUseCase(
        measurement_repository=measurement_repo,
        indicators_use_case=indicators_uc,
    )


def get_generate_executive_summary_use_case(
    indicators_uc: Annotated[
        ComputePeriodIndicatorsUseCase,
        Depends(get_compute_period_indicators_use_case),
    ],
    anomalies_uc: Annotated[
        AnalyzeAllocationAnomaliesUseCase,
        Depends(get_analyze_anomalies_use_case),
    ],
    ai_port: Annotated[AIPort, Depends(get_ai_port)],
    cache_repo: Annotated[
        AIAnalysisCacheRepository, Depends(get_ai_analysis_cache_repository)
    ],
    container: Annotated[DependencyContainer, Depends(get_container)],
) -> GenerateExecutiveSummaryUseCase:
    """Provide GenerateExecutiveSummaryUseCase.

    Args:
        indicators_uc: Indicators use case.
        anomalies_uc: Anomalies use case.
        ai_port: AI port.
        cache_repo: AI analysis cache repository.
        container: Dependency container.

    Returns:
        GenerateExecutiveSummaryUseCase: Instantiated use case.
    """
    return GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_uc,
        anomalies_use_case=anomalies_uc,
        ai_port=ai_port,
        cache_repository=cache_repo,
        settings=container.settings,
    )


# --- Dependency Type Aliases ---

AnalyzeAnomaliesUseCaseDep = Annotated[
    AnalyzeAllocationAnomaliesUseCase,
    Depends(get_analyze_anomalies_use_case),
]
GenerateExecutiveSummaryUseCaseDep = Annotated[
    GenerateExecutiveSummaryUseCase,
    Depends(get_generate_executive_summary_use_case),
]

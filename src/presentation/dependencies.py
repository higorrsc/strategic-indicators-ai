"""FastAPI dependencies and composition root wiring."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from src.allocation.application.use_cases.approve_measurement import (
    ApproveMeasurementUseCase,
)
from src.allocation.application.use_cases.list_contracts import (
    ListContractsUseCase,
)
from src.allocation.application.use_cases.list_measurements import (
    ListMeasurementsUseCase,
)
from src.allocation.application.use_cases.register_contract import (
    RegisterContractUseCase,
)
from src.allocation.application.use_cases.submit_measurement import (
    SubmitMeasurementUseCase,
)
from src.allocation.domain.repositories.contract_repository import ContractRepository
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.allocation.domain.repositories.supplier_repository import SupplierRepository
from src.allocation.infrastructure.repositories import (
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
    SqlAlchemyContractRepository,
    SqlAlchemyMeasurementRepository,
    SqlAlchemySupplierRepository,
)
from src.budgeting.application.use_cases.create_cost_center import (
    CreateCostCenterUseCase,
)
from src.budgeting.application.use_cases.get_hierarchy_budget import (
    GetHierarchyBudgetUseCase,
)
from src.budgeting.application.use_cases.set_budget_target import (
    SetBudgetTargetUseCase,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.budgeting.infrastructure.repositories import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
    SqlAlchemyBudgetRepository,
    SqlAlchemyCostCenterRepository,
)
from src.indicators.application.use_cases.compute_period_indicators import (
    ComputePeriodIndicatorsUseCase,
)
from src.indicators.application.use_cases.simulate_scenario import (
    SimulateScenarioUseCase,
)
from src.intelligence.application.ports.ai_port import AIPort
from src.intelligence.application.use_cases.analyze_allocation_anomalies import (
    AnalyzeAllocationAnomaliesUseCase,
)
from src.intelligence.application.use_cases.generate_executive_summary import (
    GenerateExecutiveSummaryUseCase,
)
from src.intelligence.infrastructure.pydantic_ai_adapter import PydanticAIAdapter
from src.shared.config.settings import Settings, get_settings
from src.shared.infrastructure.database.repositories import (
    SessionManagedBudgetRepository,
    SessionManagedContractRepository,
    SessionManagedCostCenterRepository,
    SessionManagedMeasurementRepository,
    SessionManagedSupplierRepository,
)
from src.shared.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
)


class DependencyContainer:
    """Singleton container maintaining shared repository state in memory or database."""

    def __init__(self) -> None:
        """Initialize empty container with default in-memory implementations."""
        self.settings: Settings = get_settings()
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
        self.use_database: bool = False

        self.cost_center_repo: CostCenterRepository = InMemoryCostCenterRepository()
        self.budget_repo: BudgetRepository = InMemoryBudgetRepository()
        self.supplier_repo: SupplierRepository = InMemorySupplierRepository()
        self.contract_repo: ContractRepository = InMemoryContractRepository()
        self.measurement_repo: MeasurementRepository = InMemoryMeasurementRepository()
        self.ai_port: AIPort = PydanticAIAdapter(settings=self.settings)

    async def init_database(
        self, database_url: str | None = None, echo: bool = False
    ) -> None:
        """Initialize asynchronous database engine and session-managed repositories.

        Args:
            database_url: Database connection URL, defaults to settings.
            echo: Whether to log generated SQL statements.
        """
        url = database_url or self.settings.DATABASE_URL
        self.engine = create_database_engine(url, echo=echo)
        self.session_factory = create_session_factory(self.engine)
        self.use_database = True

        self.cost_center_repo = SessionManagedCostCenterRepository(self.session_factory)
        self.budget_repo = SessionManagedBudgetRepository(self.session_factory)
        self.supplier_repo = SessionManagedSupplierRepository(self.session_factory)
        self.contract_repo = SessionManagedContractRepository(self.session_factory)
        self.measurement_repo = SessionManagedMeasurementRepository(
            self.session_factory
        )
        self.ai_port = PydanticAIAdapter(settings=self.settings)

    async def close_database(self) -> None:
        """Dispose of the database engine and clean up connection pools."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.session_factory = None
            self.use_database = False

    def reset(self) -> None:
        """Reset repository stores for testing isolation."""
        if not self.use_database:
            self.cost_center_repo = InMemoryCostCenterRepository()
            self.budget_repo = InMemoryBudgetRepository()
            self.supplier_repo = InMemorySupplierRepository()
            self.contract_repo = InMemoryContractRepository()
            self.measurement_repo = InMemoryMeasurementRepository()
        self.ai_port = PydanticAIAdapter(settings=self.settings)


_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Return the global dependency container instance.

    Returns:
        DependencyContainer: Singleton dependency container.
    """
    return _container


# --- Session Provider ---


async def get_db_session() -> AsyncGenerator[AsyncSession | None]:
    """Yield an active asynchronous database session per request if configured.

    Yields:
        AsyncSession | None: Active session or None when using in-memory mode.
    """
    container = get_container()
    if container.use_database and container.session_factory is not None:
        async with container.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    else:
        yield None


# --- Repository Providers ---


def get_cost_center_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> CostCenterRepository:
    """Provide cost center repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        CostCenterRepository: Cost center repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyCostCenterRepository(session)
    return container.cost_center_repo


def get_budget_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> BudgetRepository:
    """Provide budget target repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        BudgetRepository: Budget target repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyBudgetRepository(session)
    return container.budget_repo


def get_supplier_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> SupplierRepository:
    """Provide supplier repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        SupplierRepository: Supplier repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemySupplierRepository(session)
    return container.supplier_repo


def get_contract_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> ContractRepository:
    """Provide contract repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        ContractRepository: Contract repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyContractRepository(session)
    return container.contract_repo


def get_measurement_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> MeasurementRepository:
    """Provide measurement repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        MeasurementRepository: Measurement repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyMeasurementRepository(session)
    return container.measurement_repo


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


# --- Use Case Providers ---


def get_create_cost_center_use_case(
    repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
) -> CreateCostCenterUseCase:
    """Provide CreateCostCenterUseCase.

    Args:
        repo: Injected cost center repository.

    Returns:
        CreateCostCenterUseCase: Instantiated use case.
    """
    return CreateCostCenterUseCase(repository=repo)


def get_set_budget_target_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
) -> SetBudgetTargetUseCase:
    """Provide SetBudgetTargetUseCase.

    Args:
        budget_repo: Injected budget repository.
        cc_repo: Injected cost center repository.

    Returns:
        SetBudgetTargetUseCase: Instantiated use case.
    """
    return SetBudgetTargetUseCase(
        budget_repository=budget_repo,
        cost_center_repository=cc_repo,
    )


def get_get_hierarchy_budget_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
) -> GetHierarchyBudgetUseCase:
    """Provide GetHierarchyBudgetUseCase.

    Args:
        cc_repo: Injected cost center repository.
        budget_repo: Injected budget repository.

    Returns:
        GetHierarchyBudgetUseCase: Instantiated use case.
    """
    return GetHierarchyBudgetUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
    )


def get_register_contract_use_case(
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
    supplier_repo: Annotated[SupplierRepository, Depends(get_supplier_repository)],
) -> RegisterContractUseCase:
    """Provide RegisterContractUseCase.

    Args:
        contract_repo: Injected contract repository.
        supplier_repo: Injected supplier repository.

    Returns:
        RegisterContractUseCase: Instantiated use case.
    """
    return RegisterContractUseCase(
        contract_repository=contract_repo,
        supplier_repository=supplier_repo,
    )


def get_submit_measurement_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
) -> SubmitMeasurementUseCase:
    """Provide SubmitMeasurementUseCase.

    Args:
        measurement_repo: Injected measurement repository.
        contract_repo: Injected contract repository.

    Returns:
        SubmitMeasurementUseCase: Instantiated use case.
    """
    return SubmitMeasurementUseCase(
        measurement_repository=measurement_repo,
        contract_repository=contract_repo,
    )


def get_approve_measurement_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ApproveMeasurementUseCase:
    """Provide ApproveMeasurementUseCase.

    Args:
        measurement_repo: Injected measurement repository.

    Returns:
        ApproveMeasurementUseCase: Instantiated use case.
    """
    return ApproveMeasurementUseCase(
        measurement_repository=measurement_repo,
    )


def get_list_contracts_use_case(
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
) -> ListContractsUseCase:
    """Provide ListContractsUseCase.

    Args:
        contract_repo: Injected contract repository.

    Returns:
        ListContractsUseCase: Instantiated use case.
    """
    return ListContractsUseCase(contract_repository=contract_repo)


def get_list_measurements_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ListMeasurementsUseCase:
    """Provide ListMeasurementsUseCase.

    Args:
        measurement_repo: Injected measurement repository.

    Returns:
        ListMeasurementsUseCase: Instantiated use case.
    """
    return ListMeasurementsUseCase(measurement_repository=measurement_repo)


def get_compute_period_indicators_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ComputePeriodIndicatorsUseCase:
    """Provide ComputePeriodIndicatorsUseCase.

    Args:
        cc_repo: Cost center repository.
        budget_repo: Budget repository.
        measurement_repo: Measurement repository.

    Returns:
        ComputePeriodIndicatorsUseCase: Instantiated use case.
    """
    return ComputePeriodIndicatorsUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )


def get_simulate_scenario_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> SimulateScenarioUseCase:
    """Provide SimulateScenarioUseCase.

    Args:
        cc_repo: Cost center repository.
        budget_repo: Budget repository.
        measurement_repo: Measurement repository.

    Returns:
        SimulateScenarioUseCase: Instantiated use case.
    """
    return SimulateScenarioUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )


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
    container: Annotated[DependencyContainer, Depends(get_container)],
) -> GenerateExecutiveSummaryUseCase:
    """Provide GenerateExecutiveSummaryUseCase.

    Args:
        indicators_uc: Indicators use case.
        anomalies_uc: Anomalies use case.
        ai_port: AI port.
        container: Dependency container.

    Returns:
        GenerateExecutiveSummaryUseCase: Instantiated use case.
    """
    return GenerateExecutiveSummaryUseCase(
        indicators_use_case=indicators_uc,
        anomalies_use_case=anomalies_uc,
        ai_port=ai_port,
        settings=container.settings,
    )


# --- Dependency Type Aliases ---

CreateCostCenterUseCaseDep = Annotated[
    CreateCostCenterUseCase, Depends(get_create_cost_center_use_case)
]
SetBudgetTargetUseCaseDep = Annotated[
    SetBudgetTargetUseCase, Depends(get_set_budget_target_use_case)
]
GetHierarchyBudgetUseCaseDep = Annotated[
    GetHierarchyBudgetUseCase, Depends(get_get_hierarchy_budget_use_case)
]
RegisterContractUseCaseDep = Annotated[
    RegisterContractUseCase, Depends(get_register_contract_use_case)
]
SubmitMeasurementUseCaseDep = Annotated[
    SubmitMeasurementUseCase, Depends(get_submit_measurement_use_case)
]
ApproveMeasurementUseCaseDep = Annotated[
    ApproveMeasurementUseCase, Depends(get_approve_measurement_use_case)
]
ListContractsUseCaseDep = Annotated[
    ListContractsUseCase, Depends(get_list_contracts_use_case)
]
ListMeasurementsUseCaseDep = Annotated[
    ListMeasurementsUseCase, Depends(get_list_measurements_use_case)
]
ComputePeriodIndicatorsUseCaseDep = Annotated[
    ComputePeriodIndicatorsUseCase,
    Depends(get_compute_period_indicators_use_case),
]
SimulateScenarioUseCaseDep = Annotated[
    SimulateScenarioUseCase, Depends(get_simulate_scenario_use_case)
]
AnalyzeAnomaliesUseCaseDep = Annotated[
    AnalyzeAllocationAnomaliesUseCase,
    Depends(get_analyze_anomalies_use_case),
]
GenerateExecutiveSummaryUseCaseDep = Annotated[
    GenerateExecutiveSummaryUseCase,
    Depends(get_generate_executive_summary_use_case),
]
CostCenterRepoDep = Annotated[CostCenterRepository, Depends(get_cost_center_repository)]
ContractRepoDep = Annotated[ContractRepository, Depends(get_contract_repository)]
MeasurementRepoDep = Annotated[
    MeasurementRepository, Depends(get_measurement_repository)
]
SupplierRepoDep = Annotated[SupplierRepository, Depends(get_supplier_repository)]

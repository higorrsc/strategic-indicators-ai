"""Central dependency injection container managing shared state and lifecycle."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)
from src.allocation.domain.repositories.contract_repository import (
    ContractRepository,
)
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.allocation.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from src.allocation.infrastructure.repositories import (
    InMemoryAccountingAccountRepository,
    InMemoryContractRepository,
    InMemoryMeasurementRepository,
    InMemorySupplierRepository,
    SessionManagedAccountingAccountRepository,
    SessionManagedContractRepository,
    SessionManagedMeasurementRepository,
    SessionManagedSupplierRepository,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.budgeting.infrastructure.repositories import (
    InMemoryBudgetRepository,
    InMemoryCostCenterRepository,
    SessionManagedBudgetRepository,
    SessionManagedCostCenterRepository,
)
from src.intelligence.application.ports.ai_analysis_cache_repository import (
    AIAnalysisCacheRepository,
)
from src.intelligence.application.ports.ai_port import AIPort
from src.intelligence.infrastructure.pydantic_ai_adapter import PydanticAIAdapter
from src.intelligence.infrastructure.repositories import (
    InMemoryAIAnalysisCacheRepository,
    SessionManagedAIAnalysisCacheRepository,
)
from src.shared.config.settings import Settings, get_settings
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
        self.accounting_account_repo: AccountingAccountRepository = (
            InMemoryAccountingAccountRepository()
        )
        self.ai_cache_repo: AIAnalysisCacheRepository = (
            InMemoryAIAnalysisCacheRepository()
        )
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
        self.accounting_account_repo = SessionManagedAccountingAccountRepository(
            self.session_factory
        )
        self.ai_cache_repo = SessionManagedAIAnalysisCacheRepository(
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
            self.accounting_account_repo = InMemoryAccountingAccountRepository()
            self.ai_cache_repo = InMemoryAIAnalysisCacheRepository()
        self.ai_port = PydanticAIAdapter(settings=self.settings)


_container = DependencyContainer()


def get_container() -> DependencyContainer:
    """Return the global dependency container instance.

    Returns:
        DependencyContainer: Singleton dependency container.
    """
    return _container


def set_container(container: DependencyContainer) -> None:
    """Set global container instance for testing or runtime customization."""
    global _container
    _container = container


def reset_container() -> DependencyContainer:
    """Reset the global dependency container instance."""
    global _container
    _container = DependencyContainer()
    return _container

"""Session-managed repository wrappers for external and container access."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.allocation.domain.entities.contract import Contract
from src.allocation.domain.entities.measurement import (
    Measurement,
    MeasurementState,
)
from src.allocation.domain.entities.supplier import Supplier
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
    SqlAlchemyContractRepository,
    SqlAlchemyMeasurementRepository,
    SqlAlchemySupplierRepository,
)
from src.budgeting.domain.entities.budget_target import BudgetTarget
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.budgeting.infrastructure.repositories import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyCostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode, Period


class SessionManagedCostCenterRepository(CostCenterRepository):
    """CostCenterRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, cost_center: CostCenter) -> None:
        """Persist cost center and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            await repo.add(cost_center)
            await session.commit()

    async def get_by_id(self, cost_center_id: UUID) -> CostCenter | None:
        """Find cost center by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_by_id(cost_center_id)

    async def get_by_code(self, code: CostCenterCode) -> CostCenter | None:
        """Find cost center by code."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_by_code(code)

    async def get_children(self, parent_id: UUID) -> list[CostCenter]:
        """List active children."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_children(parent_id)

    async def get_descendants(self, root_id: UUID) -> list[CostCenter]:
        """List all descendants."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.get_descendants(root_id)

    async def list_all(self, active_only: bool = True) -> list[CostCenter]:
        """List all cost centers."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            return await repo.list_all(active_only=active_only)

    async def update(self, cost_center: CostCenter) -> None:
        """Update cost center and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyCostCenterRepository(session)
            await repo.update(cost_center)
            await session.commit()


class SessionManagedBudgetRepository(BudgetRepository):
    """BudgetRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, budget_target: BudgetTarget) -> None:
        """Persist budget target and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            await repo.add(budget_target)
            await session.commit()

    async def get_by_id(self, budget_id: UUID) -> BudgetTarget | None:
        """Find budget target by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.get_by_id(budget_id)

    async def get_by_cost_center_and_period(
        self, cost_center_id: UUID, period: Period
    ) -> list[BudgetTarget]:
        """Find targets by cost center and period."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.get_by_cost_center_and_period(cost_center_id, period)

    async def list_by_period(self, period: Period) -> list[BudgetTarget]:
        """List targets across all centers in period."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            return await repo.list_by_period(period)

    async def update(self, budget_target: BudgetTarget) -> None:
        """Update budget target and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyBudgetRepository(session)
            await repo.update(budget_target)
            await session.commit()


class SessionManagedSupplierRepository(SupplierRepository):
    """SupplierRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, supplier: Supplier) -> None:
        """Persist supplier and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemySupplierRepository(session)
            await repo.add(supplier)
            await session.commit()

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        """Find supplier by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemySupplierRepository(session)
            return await repo.get_by_id(supplier_id)

    async def list_all(self) -> list[Supplier]:
        """List all suppliers."""
        async with self._session_factory() as session:
            repo = SqlAlchemySupplierRepository(session)
            return await repo.list_all()


class SessionManagedContractRepository(ContractRepository):
    """ContractRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, contract: Contract) -> None:
        """Persist contract and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyContractRepository(session)
            await repo.add(contract)
            await session.commit()

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        """Find contract by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyContractRepository(session)
            return await repo.get_by_id(contract_id)

    async def get_by_code(self, code: str) -> Contract | None:
        """Find contract by code."""
        async with self._session_factory() as session:
            repo = SqlAlchemyContractRepository(session)
            return await repo.get_by_code(code)

    async def list_all(self, active_only: bool = True) -> list[Contract]:
        """List all contracts."""
        async with self._session_factory() as session:
            repo = SqlAlchemyContractRepository(session)
            return await repo.list_all(active_only=active_only)

    async def update(self, contract: Contract) -> None:
        """Update contract and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyContractRepository(session)
            await repo.update(contract)
            await session.commit()


class SessionManagedMeasurementRepository(MeasurementRepository):
    """MeasurementRepository wrapper that executes each operation in a session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize with an async session factory."""
        self._session_factory = session_factory

    async def add(self, measurement: Measurement) -> None:
        """Persist measurement and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyMeasurementRepository(session)
            await repo.add(measurement)
            await session.commit()

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None:
        """Find measurement by id."""
        async with self._session_factory() as session:
            repo = SqlAlchemyMeasurementRepository(session)
            return await repo.get_by_id(measurement_id)

    async def list_by_period(
        self, period: Period, state: MeasurementState | None = None
    ) -> list[Measurement]:
        """List measurements by period and state."""
        async with self._session_factory() as session:
            repo = SqlAlchemyMeasurementRepository(session)
            return await repo.list_by_period(period, state=state)

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]:
        """List measurements by contract."""
        async with self._session_factory() as session:
            repo = SqlAlchemyMeasurementRepository(session)
            return await repo.list_by_contract(contract_id)

    async def update(self, measurement: Measurement) -> None:
        """Update measurement and commit transaction."""
        async with self._session_factory() as session:
            repo = SqlAlchemyMeasurementRepository(session)
            await repo.update(measurement)
            await session.commit()

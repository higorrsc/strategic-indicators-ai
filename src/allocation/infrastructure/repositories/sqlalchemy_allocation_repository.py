"""SQLAlchemy repository implementations for Cost Allocation Bounded Context."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.entities.measurement import (
    AllocationEntry,
    Measurement,
    MeasurementState,
)
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import (
    AllocationDomainError,
    ContractNotFoundError,
    DuplicateAccountCodeError,
    MeasurementNotFoundError,
)
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
from src.allocation.infrastructure.database.models import (
    AccountingAccountModel,
    AllocationEntryModel,
    ContractAllocationModel,
    ContractModel,
    MeasurementModel,
    SupplierModel,
)
from src.shared.domain.value_objects import AccountCode, Money, Percentage, Period


def _to_supplier_entity(model: SupplierModel) -> Supplier:
    """Map a SupplierModel to a pure Supplier domain entity."""
    return Supplier(
        id=model.id,
        name=model.name,
        tax_id=model.tax_id,
    )


def _to_accounting_account_entity(model: AccountingAccountModel) -> AccountingAccount:
    """Map an AccountingAccountModel to a pure AccountingAccount domain entity."""
    return AccountingAccount(
        id=model.id,
        code=AccountCode(model.code),
        name=model.name,
        description=model.description,
        is_active=model.is_active,
    )


def _to_contract_entity(model: ContractModel) -> Contract:
    """Map a ContractModel to a pure Contract domain entity."""
    default_allocations = [
        AllocationShare(
            cost_center_id=a.cost_center_id,
            percentage=Percentage(a.percentage),
            accounting_account_id=a.accounting_account_id,
        )
        for a in model.default_allocations
    ]
    return Contract(
        id=model.id,
        code=model.code,
        supplier_id=model.supplier_id,
        title=model.title,
        default_allocations=default_allocations,
        is_active=model.is_active,
    )


def _to_measurement_entity(model: MeasurementModel) -> Measurement:
    """Map a MeasurementModel to a pure Measurement aggregate domain entity."""
    entries = [
        AllocationEntry(
            id=e.id,
            cost_center_id=e.cost_center_id,
            amount=Money(e.amount, e.currency),
            percentage=Percentage(e.percentage),
            accounting_account_id=e.accounting_account_id,
        )
        for e in model.entries
    ]
    return Measurement(
        id=model.id,
        contract_id=model.contract_id,
        period=Period.from_string(model.period),
        description=model.description,
        gross_amount=Money(model.gross_amount, model.currency),
        state=MeasurementState(model.state),
        entries=entries,
    )


class SqlAlchemySupplierRepository(SupplierRepository):
    """SQLAlchemy implementation of SupplierRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def add(self, supplier: Supplier) -> None:
        """Persist a new supplier.

        Args:
            supplier: Supplier entity to add.
        """
        model = SupplierModel(
            id=supplier.id,
            name=supplier.name,
            tax_id=supplier.tax_id,
        )
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        """Find supplier by identifier.

        Args:
            supplier_id: Supplier UUID.

        Returns:
            Supplier if found, None otherwise.
        """
        stmt = select(SupplierModel).where(SupplierModel.id == supplier_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_supplier_entity(model) if model else None

    async def list_all(self) -> list[Supplier]:
        """List all suppliers.

        Returns:
            List of suppliers.
        """
        stmt = select(SupplierModel)
        result = await self._session.execute(stmt)
        return [_to_supplier_entity(m) for m in result.scalars().all()]


class SqlAlchemyContractRepository(ContractRepository):
    """SQLAlchemy implementation of ContractRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def add(self, contract: Contract) -> None:
        """Persist a new contract with default allocations.

        Args:
            contract: Contract entity to add.
        """
        existing = await self.get_by_code(contract.code)
        if existing is not None:
            raise AllocationDomainError(
                f"Contract with code '{contract.code}' already exists."
            )

        model = ContractModel(
            id=contract.id,
            code=contract.code,
            supplier_id=contract.supplier_id,
            title=contract.title,
            is_active=contract.is_active,
        )
        for share in contract.default_allocations:
            alloc_model = ContractAllocationModel(
                id=uuid4(),
                contract_id=contract.id,
                cost_center_id=share.cost_center_id,
                percentage=share.percentage.value,
                accounting_account_id=share.accounting_account_id,
            )
            model.default_allocations.append(alloc_model)

        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        """Find contract by identifier.

        Args:
            contract_id: Contract UUID.

        Returns:
            Contract if found, None otherwise.
        """
        stmt = select(ContractModel).where(ContractModel.id == contract_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_contract_entity(model) if model else None

    async def get_by_code(self, code: str) -> Contract | None:
        """Find contract by alphanumeric code.

        Args:
            code: Contract code.

        Returns:
            Contract if found, None otherwise.
        """
        stmt = select(ContractModel).where(ContractModel.code == code)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_contract_entity(model) if model else None

    async def list_all(self, active_only: bool = True) -> list[Contract]:
        """List all contracts.

        Args:
            active_only: Whether to filter active contracts only.

        Returns:
            List of contracts.
        """
        stmt = select(ContractModel)
        if active_only:
            stmt = stmt.where(ContractModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [_to_contract_entity(m) for m in result.scalars().all()]

    async def update(self, contract: Contract) -> None:
        """Update existing contract.

        Args:
            contract: Modified contract entity.
        """
        stmt = select(ContractModel).where(ContractModel.id == contract.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ContractNotFoundError(f"Contract ID {contract.id} does not exist.")
        model.title = contract.title
        model.is_active = contract.is_active
        await self._session.flush()


class SqlAlchemyMeasurementRepository(MeasurementRepository):
    """SQLAlchemy implementation of MeasurementRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def add(self, measurement: Measurement) -> None:
        """Persist a new measurement with its allocation entries.

        Args:
            measurement: Measurement entity to add.
        """
        model = MeasurementModel(
            id=measurement.id,
            contract_id=measurement.contract_id,
            period=measurement.period.value,
            description=measurement.description,
            gross_amount=measurement.gross_amount.amount,
            currency=measurement.gross_amount.currency,
            state=measurement.state.value,
        )
        for entry in measurement.entries:
            entry_model = AllocationEntryModel(
                id=entry.id,
                measurement_id=measurement.id,
                cost_center_id=entry.cost_center_id,
                amount=entry.amount.amount,
                currency=entry.amount.currency,
                percentage=entry.percentage.value,
                accounting_account_id=entry.accounting_account_id,
            )
            model.entries.append(entry_model)

        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None:
        """Find measurement by identifier.

        Args:
            measurement_id: Measurement UUID.

        Returns:
            Measurement if found, None otherwise.
        """
        stmt = select(MeasurementModel).where(MeasurementModel.id == measurement_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_measurement_entity(model) if model else None

    async def list_by_period(
        self, period: Period, state: MeasurementState | None = None
    ) -> list[Measurement]:
        """List measurements matching a fiscal period.

        Args:
            period: Fiscal period.
            state: Optional state filter.

        Returns:
            List of measurements.
        """
        stmt = select(MeasurementModel).where(MeasurementModel.period == period.value)
        if state is not None:
            stmt = stmt.where(MeasurementModel.state == state.value)
        result = await self._session.execute(stmt)
        return [_to_measurement_entity(m) for m in result.scalars().all()]

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]:
        """List measurements associated with a contract.

        Args:
            contract_id: Contract UUID.

        Returns:
            List of measurements.
        """
        stmt = select(MeasurementModel).where(
            MeasurementModel.contract_id == contract_id
        )
        result = await self._session.execute(stmt)
        return [_to_measurement_entity(m) for m in result.scalars().all()]

    async def find(
        self,
        period: Period | None = None,
        contract_id: UUID | None = None,
        state: MeasurementState | None = None,
    ) -> list[Measurement]:
        """Find measurements matching optional criteria.

        Args:
            period: Optional fiscal period filter.
            contract_id: Optional contract UUID filter.
            state: Optional measurement lifecycle state filter.

        Returns:
            List of matching measurements.
        """
        stmt = select(MeasurementModel)
        if period is not None:
            stmt = stmt.where(MeasurementModel.period == period.value)
        if contract_id is not None:
            stmt = stmt.where(MeasurementModel.contract_id == contract_id)
        if state is not None:
            stmt = stmt.where(MeasurementModel.state == state.value)
        result = await self._session.execute(stmt)
        return [_to_measurement_entity(m) for m in result.scalars().all()]

    async def update(self, measurement: Measurement) -> None:
        """Update existing measurement and sync entries.

        Args:
            measurement: Modified measurement entity.
        """
        stmt = select(MeasurementModel).where(MeasurementModel.id == measurement.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise MeasurementNotFoundError(
                f"Measurement ID {measurement.id} does not exist."
            )
        model.state = measurement.state.value
        model.description = measurement.description
        model.gross_amount = measurement.gross_amount.amount
        model.currency = measurement.gross_amount.currency
        model.period = measurement.period.value

        # Sync entries
        model.entries.clear()
        for entry in measurement.entries:
            model.entries.append(
                AllocationEntryModel(
                    id=entry.id,
                    measurement_id=measurement.id,
                    cost_center_id=entry.cost_center_id,
                    amount=entry.amount.amount,
                    currency=entry.amount.currency,
                    percentage=entry.percentage.value,
                    accounting_account_id=entry.accounting_account_id,
                )
            )
        await self._session.flush()


class SqlAlchemyAccountingAccountRepository(AccountingAccountRepository):
    """SQLAlchemy implementation of AccountingAccountRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with active asynchronous database session.

        Args:
            session: Active SQLAlchemy AsyncSession.
        """
        self._session = session

    async def save(self, account: AccountingAccount) -> None:
        """Persist a new or updated accounting account.

        Args:
            account: AccountingAccount entity to persist.
        """
        stmt = select(AccountingAccountModel).where(
            AccountingAccountModel.id == account.id
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        if model is None:
            dup_stmt = select(AccountingAccountModel).where(
                AccountingAccountModel.code == account.code.value
            )
            dup_res = await self._session.execute(dup_stmt)
            if dup_res.scalar_one_or_none() is not None:
                raise DuplicateAccountCodeError(
                    f"Accounting account with code '{account.code}' already exists."
                )
            model = AccountingAccountModel(
                id=account.id,
                code=account.code.value,
                name=account.name,
                description=account.description,
                is_active=account.is_active,
            )
            self._session.add(model)
        else:
            model.name = account.name
            model.description = account.description
            model.is_active = account.is_active
        await self._session.flush()

    async def get_by_id(self, account_id: UUID) -> AccountingAccount | None:
        """Find accounting account by UUID.

        Args:
            account_id: Account UUID.

        Returns:
            AccountingAccount or None.
        """
        stmt = select(AccountingAccountModel).where(
            AccountingAccountModel.id == account_id
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _to_accounting_account_entity(model) if model else None

    async def get_by_code(self, code: AccountCode) -> AccountingAccount | None:
        """Find accounting account by code.

        Args:
            code: AccountCode value object.

        Returns:
            AccountingAccount or None.
        """
        stmt = select(AccountingAccountModel).where(
            AccountingAccountModel.code == code.value
        )
        res = await self._session.execute(stmt)
        model = res.scalar_one_or_none()
        return _to_accounting_account_entity(model) if model else None

    async def list_all(
        self,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AccountingAccount]:
        """List accounting accounts with active filter and pagination.

        Args:
            active_only: Filter by active status.
            offset: Items to skip.
            limit: Maximum items.

        Returns:
            List of accounting accounts.
        """
        stmt = select(AccountingAccountModel)
        if active_only:
            stmt = stmt.where(AccountingAccountModel.is_active.is_(True))
        stmt = stmt.order_by(AccountingAccountModel.code).offset(offset).limit(limit)
        res = await self._session.execute(stmt)
        return [_to_accounting_account_entity(m) for m in res.scalars().all()]

    async def count(self, active_only: bool = True) -> int:
        """Count total accounting accounts.

        Args:
            active_only: Filter by active status.

        Returns:
            Total count.
        """
        stmt = select(func.count(AccountingAccountModel.id))
        if active_only:
            stmt = stmt.where(AccountingAccountModel.is_active.is_(True))
        res = await self._session.execute(stmt)
        return res.scalar_one() or 0

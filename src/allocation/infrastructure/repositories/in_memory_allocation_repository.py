"""In-memory repository test doubles for cost allocation domain."""

from __future__ import annotations

from uuid import UUID

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.contract import Contract
from src.allocation.domain.entities.measurement import Measurement, MeasurementState
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
from src.shared.domain.value_objects import AccountCode, Period


class InMemorySupplierRepository(SupplierRepository):
    """In-memory test double implementation for SupplierRepository."""

    def __init__(self) -> None:
        """Initialize in-memory supplier storage."""
        self._suppliers: dict[UUID, Supplier] = {}

    async def add(self, supplier: Supplier) -> None:
        """Add supplier to in-memory store.

        Args:
            supplier: Supplier entity to add.
        """
        self._suppliers[supplier.id] = supplier

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        """Find supplier by ID.

        Args:
            supplier_id: Supplier UUID.

        Returns:
            Supplier if found, None otherwise.
        """
        return self._suppliers.get(supplier_id)

    async def list_all(self) -> list[Supplier]:
        """List all stored suppliers.

        Returns:
            List of suppliers.
        """
        return list(self._suppliers.values())


class InMemoryContractRepository(ContractRepository):
    """In-memory test double implementation for ContractRepository."""

    def __init__(self) -> None:
        """Initialize in-memory contract storage."""
        self._contracts: dict[UUID, Contract] = {}

    async def add(self, contract: Contract) -> None:
        """Add contract verifying code uniqueness.

        Args:
            contract: Contract entity to add.
        """
        for c in self._contracts.values():
            if c.code == contract.code:
                raise AllocationDomainError(
                    f"Contract with code '{contract.code}' already exists."
                )
        self._contracts[contract.id] = contract

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        """Find contract by ID.

        Args:
            contract_id: Contract UUID.

        Returns:
            Contract if found, None otherwise.
        """
        return self._contracts.get(contract_id)

    async def get_by_code(self, code: str) -> Contract | None:
        """Find contract by alphanumeric code.

        Args:
            code: Contract code.

        Returns:
            Contract if found, None otherwise.
        """
        for c in self._contracts.values():
            if c.code == code:
                return c
        return None

    async def list_all(self, active_only: bool = True) -> list[Contract]:
        """List all contracts.

        Args:
            active_only: Whether to filter active only.

        Returns:
            List of contracts.
        """
        if active_only:
            return [c for c in self._contracts.values() if c.is_active]
        return list(self._contracts.values())

    async def update(self, contract: Contract) -> None:
        """Update existing contract.

        Args:
            contract: Modified contract entity.
        """
        if contract.id not in self._contracts:
            raise ContractNotFoundError(f"Contract with id {contract.id} not found.")
        self._contracts[contract.id] = contract


class InMemoryMeasurementRepository(MeasurementRepository):
    """In-memory test double implementation for MeasurementRepository."""

    def __init__(self) -> None:
        """Initialize in-memory measurement storage."""
        self._measurements: dict[UUID, Measurement] = {}

    async def add(self, measurement: Measurement) -> None:
        """Add measurement to in-memory store.

        Args:
            measurement: Measurement entity to add.
        """
        self._measurements[measurement.id] = measurement

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None:
        """Find measurement by ID.

        Args:
            measurement_id: Measurement UUID.

        Returns:
            Measurement if found, None otherwise.
        """
        return self._measurements.get(measurement_id)

    async def list_by_period(
        self, period: Period, state: MeasurementState | None = None
    ) -> list[Measurement]:
        """List measurements matching period and optional state.

        Args:
            period: Fiscal period.
            state: Optional state filter.

        Returns:
            List of measurements.
        """
        return [
            m
            for m in self._measurements.values()
            if m.period == period and (state is None or m.state == state)
        ]

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]:
        """List measurements associated with a contract ID.

        Args:
            contract_id: Contract UUID.

        Returns:
            List of measurements.
        """
        return [m for m in self._measurements.values() if m.contract_id == contract_id]

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
        results = list(self._measurements.values())
        if period is not None:
            results = [m for m in results if m.period == period]
        if contract_id is not None:
            results = [m for m in results if m.contract_id == contract_id]
        if state is not None:
            results = [m for m in results if m.state == state]
        return results

    async def update(self, measurement: Measurement) -> None:
        """Update existing measurement.

        Args:
            measurement: Modified measurement entity.
        """
        if measurement.id not in self._measurements:
            raise MeasurementNotFoundError(
                f"Measurement with id {measurement.id} not found."
            )
        self._measurements[measurement.id] = measurement


class InMemoryAccountingAccountRepository(AccountingAccountRepository):
    """In-memory test double implementation for AccountingAccountRepository."""

    def __init__(self) -> None:
        """Initialize in-memory accounting accounts storage."""
        self._accounts: dict[UUID, AccountingAccount] = {}

    async def save(self, account: AccountingAccount) -> None:
        """Persist accounting account ensuring code uniqueness.

        Args:
            account: Accounting account entity to save.
        """
        for existing in self._accounts.values():
            if existing.id != account.id and existing.code == account.code:
                raise DuplicateAccountCodeError(
                    f"Accounting account with code '{account.code}' already exists."
                )
        self._accounts[account.id] = account

    async def get_by_id(self, account_id: UUID) -> AccountingAccount | None:
        """Find accounting account by UUID.

        Args:
            account_id: Account UUID.

        Returns:
            AccountingAccount or None.
        """
        return self._accounts.get(account_id)

    async def get_by_code(self, code: AccountCode) -> AccountingAccount | None:
        """Find accounting account by code.

        Args:
            code: AccountCode value object.

        Returns:
            AccountingAccount or None.
        """
        for account in self._accounts.values():
            if account.code == code:
                return account
        return None

    async def list_all(
        self,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AccountingAccount]:
        """List accounting accounts with pagination and active filter.

        Args:
            active_only: Filter by active status.
            offset: Items to skip.
            limit: Maximum items.

        Returns:
            Paginated list of accounts.
        """
        accounts = list(self._accounts.values())
        if active_only:
            accounts = [a for a in accounts if a.is_active]
        accounts.sort(key=lambda a: a.code.value)
        return accounts[offset : offset + limit]

    async def count(self, active_only: bool = True) -> int:
        """Count total accounting accounts.

        Args:
            active_only: Filter by active status.

        Returns:
            Total count.
        """
        if active_only:
            return sum(1 for a in self._accounts.values() if a.is_active)
        return len(self._accounts)


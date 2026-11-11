from __future__ import annotations

from uuid import UUID

from src.allocation.domain.entities.contract import Contract
from src.allocation.domain.entities.measurement import Measurement, MeasurementState
from src.allocation.domain.entities.supplier import Supplier
from src.allocation.domain.exceptions import (
    AllocationDomainError,
    ContractNotFoundError,
    MeasurementNotFoundError,
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
from src.shared.domain.value_objects import Period


class InMemorySupplierRepository(SupplierRepository):
    """In-memory test double implementation for SupplierRepository."""

    def __init__(self) -> None:
        self._suppliers: dict[UUID, Supplier] = {}

    async def add(self, supplier: Supplier) -> None:
        self._suppliers[supplier.id] = supplier

    async def get_by_id(self, supplier_id: UUID) -> Supplier | None:
        return self._suppliers.get(supplier_id)

    async def list_all(self) -> list[Supplier]:
        return list(self._suppliers.values())


class InMemoryContractRepository(ContractRepository):
    """In-memory test double implementation for ContractRepository."""

    def __init__(self) -> None:
        self._contracts: dict[UUID, Contract] = {}

    async def add(self, contract: Contract) -> None:
        for c in self._contracts.values():
            if c.code == contract.code:
                raise AllocationDomainError(
                    f"Contract with code '{contract.code}' already exists."
                )
        self._contracts[contract.id] = contract

    async def get_by_id(self, contract_id: UUID) -> Contract | None:
        return self._contracts.get(contract_id)

    async def get_by_code(self, code: str) -> Contract | None:
        for c in self._contracts.values():
            if c.code == code:
                return c
        return None

    async def list_all(self, active_only: bool = True) -> list[Contract]:
        if active_only:
            return [c for c in self._contracts.values() if c.is_active]
        return list(self._contracts.values())

    async def update(self, contract: Contract) -> None:
        if contract.id not in self._contracts:
            raise ContractNotFoundError(f"Contract with id {contract.id} not found.")
        self._contracts[contract.id] = contract


class InMemoryMeasurementRepository(MeasurementRepository):
    """In-memory test double implementation for MeasurementRepository."""

    def __init__(self) -> None:
        self._measurements: dict[UUID, Measurement] = {}

    async def add(self, measurement: Measurement) -> None:
        self._measurements[measurement.id] = measurement

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None:
        return self._measurements.get(measurement_id)

    async def list_by_period(
        self, period: Period, state: MeasurementState | None = None
    ) -> list[Measurement]:
        return [
            m
            for m in self._measurements.values()
            if m.period == period and (state is None or m.state == state)
        ]

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]:
        return [m for m in self._measurements.values() if m.contract_id == contract_id]

    async def update(self, measurement: Measurement) -> None:
        if measurement.id not in self._measurements:
            raise MeasurementNotFoundError(
                f"Measurement with id {measurement.id} not found."
            )
        self._measurements[measurement.id] = measurement

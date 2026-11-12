"""Repository interface for Measurement persistence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.measurement import Measurement, MeasurementState
from src.shared.domain.value_objects import Period


class MeasurementRepository(Protocol):
    """Repository abstraction for Measurement persistence."""

    async def add(self, measurement: Measurement) -> None:
        """Persist a new measurement.

        Args:
            measurement: Measurement entity to add.
        """
        ...

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None:
        """Find measurement by identifier.

        Args:
            measurement_id: Measurement UUID.

        Returns:
            Measurement if found, None otherwise.
        """
        ...

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
        ...

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]:
        """List measurements associated with a contract.

        Args:
            contract_id: Contract UUID.

        Returns:
            List of measurements.
        """
        ...

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
        ...

    async def update(self, measurement: Measurement) -> None:
        """Update existing measurement.

        Args:
            measurement: Modified measurement entity.
        """
        ...

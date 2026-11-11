from __future__ import annotations

from typing import Protocol
from uuid import UUID

from src.allocation.domain.entities.measurement import Measurement, MeasurementState
from src.shared.domain.value_objects import Period


class MeasurementRepository(Protocol):
    """Repository abstraction for Measurement persistence."""

    async def add(self, measurement: Measurement) -> None: ...

    async def get_by_id(self, measurement_id: UUID) -> Measurement | None: ...

    async def list_by_period(
        self, period: Period, state: MeasurementState | None = None
    ) -> list[Measurement]: ...

    async def list_by_contract(self, contract_id: UUID) -> list[Measurement]: ...

    async def update(self, measurement: Measurement) -> None: ...

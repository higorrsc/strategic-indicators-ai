"""Use case for querying and listing financial measurements."""

from __future__ import annotations

from src.allocation.application.dto import (
    AllocationEntryDTO,
    ListMeasurementsQuery,
    MeasurementDTO,
    PaginatedResultDTO,
)
from src.allocation.domain.entities.measurement import MeasurementState
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.shared.domain.value_objects import Period


class ListMeasurementsUseCase:
    """Orchestrates querying measurements with filters and pagination."""

    def __init__(self, measurement_repository: MeasurementRepository) -> None:
        """Initialize use case with measurement repository.

        Args:
            measurement_repository: Repository for measurement persistence.
        """
        self._measurement_repository = measurement_repository

    async def execute(
        self, query: ListMeasurementsQuery | None = None
    ) -> PaginatedResultDTO[MeasurementDTO]:
        """Query measurements matching optional filter criteria and pagination.

        Args:
            query: Optional filter and pagination parameters.

        Returns:
            PaginatedResultDTO[MeasurementDTO]: Paginated measurements result.
        """
        q = query or ListMeasurementsQuery()
        period_vo = Period.from_string(q.period) if q.period else None
        state_vo = MeasurementState(q.state) if q.state else None

        measurements = await self._measurement_repository.find(
            period=period_vo,
            contract_id=q.contract_id,
            state=state_vo,
        )

        total_items = len(measurements)
        offset = (q.page - 1) * q.per_page
        sliced = measurements[offset : offset + q.per_page]

        dtos = [
            MeasurementDTO(
                id=m.id,
                contract_id=m.contract_id,
                period=str(m.period),
                description=m.description,
                gross_amount=m.gross_amount.amount,
                currency=m.gross_amount.currency,
                state=m.state.value,
                entries=[
                    AllocationEntryDTO(
                        id=e.id,
                        cost_center_id=e.cost_center_id,
                        amount=e.amount.amount,
                        percentage=e.percentage.value,
                        currency=e.amount.currency,
                    )
                    for e in m.entries
                ],
            )
            for m in sliced
        ]
        return PaginatedResultDTO(
            items=dtos,
            total_items=total_items,
            page=q.page,
            per_page=q.per_page,
        )

from src.allocation.application.dto import (
    AllocationEntryDTO,
    ApproveMeasurementCommand,
    MeasurementDTO,
)
from src.allocation.domain.exceptions import MeasurementNotFoundError
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)


class ApproveMeasurementUseCase:
    """Orchestrates reviewing and approving a submitted measurement."""

    def __init__(self, measurement_repository: MeasurementRepository) -> None:
        self._measurement_repository = measurement_repository

    async def execute(self, command: ApproveMeasurementCommand) -> MeasurementDTO:
        measurement = await self._measurement_repository.get_by_id(
            command.measurement_id
        )
        if measurement is None:
            raise MeasurementNotFoundError(
                f"Measurement with ID {command.measurement_id} not found."
            )

        measurement.approve()
        await self._measurement_repository.update(measurement)

        return MeasurementDTO(
            id=measurement.id,
            contract_id=measurement.contract_id,
            period=str(measurement.period),
            description=measurement.description,
            gross_amount=measurement.gross_amount.amount,
            currency=measurement.gross_amount.currency,
            state=measurement.state.value,
            entries=[
                AllocationEntryDTO(
                    id=e.id,
                    cost_center_id=e.cost_center_id,
                    amount=e.amount.amount,
                    percentage=e.percentage.value,
                    currency=e.amount.currency,
                )
                for e in measurement.entries
            ],
        )

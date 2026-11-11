from decimal import Decimal

from src.allocation.application.dto import (
    AllocationEntryDTO,
    MeasurementDTO,
    SubmitMeasurementCommand,
)
from src.allocation.domain.entities.contract import AllocationShare
from src.allocation.domain.entities.measurement import Measurement
from src.allocation.domain.exceptions import (
    AllocationDomainError,
    ContractNotFoundError,
)
from src.allocation.domain.repositories.contract_repository import (
    ContractRepository,
)
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.shared.domain.value_objects import Money, Percentage, Period


class SubmitMeasurementUseCase:
    """Orchestrates creating and submitting a measurement with flexible allocation."""

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        contract_repository: ContractRepository,
    ) -> None:
        self._measurement_repository = measurement_repository
        self._contract_repository = contract_repository

    async def execute(self, command: SubmitMeasurementCommand) -> MeasurementDTO:
        contract = await self._contract_repository.get_by_id(command.contract_id)
        if contract is None:
            raise ContractNotFoundError(
                f"Contract with ID {command.contract_id} not found."
            )

        # Determine shares: custom override or contract default
        if command.custom_allocations:
            shares = [
                AllocationShare(
                    cost_center_id=s.cost_center_id,
                    percentage=Percentage.from_number(s.percentage),
                )
                for s in command.custom_allocations
            ]
        elif contract.default_allocations:
            shares = contract.default_allocations
        else:
            raise AllocationDomainError(
                "No allocation rules provided and contract has no default allocation."
            )

        period = Period.from_string(command.period)
        gross_amount = Money(
            amount=Decimal(str(command.gross_amount)),
            currency=command.currency,
        )

        entries = ExactPennyAllocator.allocate(gross_amount, shares)

        measurement = Measurement(
            contract_id=contract.id,
            period=period,
            description=command.description,
            gross_amount=gross_amount,
        )
        measurement.set_entries(entries)
        measurement.submit()

        await self._measurement_repository.add(measurement)

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

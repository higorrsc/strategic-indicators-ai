"""Use case for creating and submitting a measurement expense."""

from decimal import Decimal

from src.allocation.application.dto import (
    AllocationEntryDTO,
    MeasurementDTO,
    SubmitMeasurementCommand,
)
from src.allocation.domain.entities.contract import AllocationShare
from src.allocation.domain.entities.measurement import Measurement
from src.allocation.domain.exceptions import (
    AccountingAccountNotFoundError,
    AllocationDomainError,
    ContractNotFoundError,
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
from src.allocation.domain.services.allocator import ExactPennyAllocator
from src.shared.domain.value_objects import Money, Percentage, Period


class SubmitMeasurementUseCase:
    """Orchestrates creating and submitting a measurement with flexible allocation."""

    def __init__(
        self,
        measurement_repository: MeasurementRepository,
        contract_repository: ContractRepository,
        accounting_account_repository: AccountingAccountRepository | None = None,
    ) -> None:
        """Initialize use case with repositories.

        Args:
            measurement_repository: Repository for measurement persistence.
            contract_repository: Repository for contract lookups.
            accounting_account_repository: Optional repository for accounting accounts.
        """
        self._measurement_repository = measurement_repository
        self._contract_repository = contract_repository
        self._accounting_account_repository = accounting_account_repository

    async def execute(self, command: SubmitMeasurementCommand) -> MeasurementDTO:
        """Create and submit a measurement with calculated exact allocation lines.

        Args:
            command: Submission command payload.

        Returns:
            MeasurementDTO: The submitted measurement and reconciled allocation entries.
        """
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
                    accounting_account_id=s.accounting_account_id,
                )
                for s in command.custom_allocations
            ]
        elif contract.default_allocations:
            shares = contract.default_allocations
        else:
            raise AllocationDomainError(
                "No allocation rules provided and contract has no default allocation."
            )

        if self._accounting_account_repository is not None:
            for s in shares:
                if s.accounting_account_id is not None:
                    acc = await self._accounting_account_repository.get_by_id(
                        s.accounting_account_id
                    )
                    if acc is None:
                        raise AccountingAccountNotFoundError(
                            f"Accounting account ID {s.accounting_account_id} "
                            "not found."
                        )
                    if not acc.is_active:
                        raise AllocationDomainError(
                            f"Accounting account '{acc.code}' is inactive."
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
                    accounting_account_id=e.accounting_account_id,
                )
                for e in measurement.entries
            ],
        )

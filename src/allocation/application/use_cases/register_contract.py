"""Use case for registering vendor contracts."""

from src.allocation.application.dto import (
    AllocationShareDTO,
    ContractDTO,
    RegisterContractCommand,
)
from src.allocation.domain.entities.contract import AllocationShare, Contract
from src.allocation.domain.exceptions import SupplierNotFoundError
from src.allocation.domain.repositories.contract_repository import (
    ContractRepository,
)
from src.allocation.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from src.shared.domain.value_objects import Percentage


class RegisterContractUseCase:
    """Orchestrates vendor contract registration with default allocations."""

    def __init__(
        self,
        contract_repository: ContractRepository,
        supplier_repository: SupplierRepository,
    ) -> None:
        """Initialize use case with contract and supplier repositories.

        Args:
            contract_repository: Repository for contract persistence.
            supplier_repository: Repository for supplier verification.
        """
        self._contract_repository = contract_repository
        self._supplier_repository = supplier_repository

    async def execute(self, command: RegisterContractCommand) -> ContractDTO:
        """Register a vendor contract and validate default allocation shares.

        Args:
            command: Contract registration command payload.

        Returns:
            ContractDTO: The created contract representation.
        """
        supplier = await self._supplier_repository.get_by_id(command.supplier_id)
        if supplier is None:
            raise SupplierNotFoundError(
                f"Supplier with ID {command.supplier_id} not found."
            )

        shares = [
            AllocationShare(
                cost_center_id=s.cost_center_id,
                percentage=Percentage.from_number(s.percentage),
            )
            for s in command.default_allocations
        ]

        contract = Contract(
            code=command.code,
            supplier_id=supplier.id,
            title=command.title,
            default_allocations=shares,
        )

        await self._contract_repository.add(contract)

        return ContractDTO(
            id=contract.id,
            code=contract.code,
            supplier_id=contract.supplier_id,
            title=contract.title,
            default_allocations=[
                AllocationShareDTO(
                    cost_center_id=s.cost_center_id,
                    percentage=s.percentage.value,
                )
                for s in contract.default_allocations
            ],
            is_active=contract.is_active,
        )

"""Use case for creating and persisting a cost center."""

from src.budgeting.application.dto import (
    CostCenterDTO,
    CreateCostCenterCommand,
)
from src.budgeting.domain.entities.cost_center import CostCenter
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.shared.domain.value_objects import CostCenterCode


class CreateCostCenterUseCase:
    """Orchestrates creation and persistence of a new Cost Center."""

    def __init__(self, repository: CostCenterRepository) -> None:
        """Initialize use case with repository dependency.

        Args:
            repository: Cost center repository instance.
        """
        self._repository = repository

    async def execute(self, command: CreateCostCenterCommand) -> CostCenterDTO:
        """Execute creation of cost center.

        Args:
            command: Creation input payload.

        Returns:
            CostCenterDTO: The created cost center data.
        """
        code = CostCenterCode(command.code)
        cost_center = CostCenter(
            code=code,
            name=command.name,
            parent_id=command.parent_id,
        )
        await self._repository.add(cost_center)
        return CostCenterDTO(
            id=cost_center.id,
            code=str(cost_center.code),
            name=cost_center.name,
            parent_id=cost_center.parent_id,
            is_active=cost_center.is_active,
        )

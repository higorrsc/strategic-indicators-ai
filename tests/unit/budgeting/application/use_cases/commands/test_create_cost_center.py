import pytest

from src.budgeting.application.dto import CreateCostCenterCommand
from src.budgeting.application.use_cases.commands import CreateCostCenterUseCase
from src.budgeting.domain.exceptions import DuplicateCostCenterCodeError
from src.budgeting.infrastructure.repositories.in_memory_budgeting_repository import (
    InMemoryCostCenterRepository,
)


@pytest.mark.asyncio
async def test_should_create_cost_center_successfully() -> None:
    cc_repo = InMemoryCostCenterRepository()
    use_case = CreateCostCenterUseCase(cc_repo)

    result = await use_case.execute(
        CreateCostCenterCommand(code="1.0", name="Executive Board")
    )
    assert result.code == "1.0"
    assert result.name == "Executive Board"
    assert result.is_active is True


@pytest.mark.asyncio
async def test_should_reject_duplicate_code() -> None:
    cc_repo = InMemoryCostCenterRepository()
    use_case = CreateCostCenterUseCase(cc_repo)

    await use_case.execute(CreateCostCenterCommand(code="1.0", name="Board A"))
    with pytest.raises(DuplicateCostCenterCodeError):
        await use_case.execute(CreateCostCenterCommand(code="1.0", name="Board B"))

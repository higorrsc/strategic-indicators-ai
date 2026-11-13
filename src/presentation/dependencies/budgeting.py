"""Budgeting dependency providers and type annotations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.budgeting.application.use_cases.commands import (
    CreateCostCenterUseCase,
    SetBudgetTargetUseCase,
)
from src.budgeting.application.use_cases.queries import (
    GetHierarchyBudgetUseCase,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.budgeting.infrastructure.repositories import (
    SqlAlchemyBudgetRepository,
    SqlAlchemyCostCenterRepository,
)

from .container import DependencyContainer, get_container
from .database import get_db_session


def get_cost_center_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> CostCenterRepository:
    """Provide cost center repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        CostCenterRepository: Cost center repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyCostCenterRepository(session)
    return container.cost_center_repo


def get_budget_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> BudgetRepository:
    """Provide budget target repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        BudgetRepository: Budget target repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyBudgetRepository(session)
    return container.budget_repo


def get_create_cost_center_use_case(
    repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
) -> CreateCostCenterUseCase:
    """Provide CreateCostCenterUseCase.

    Args:
        repo: Injected cost center repository.

    Returns:
        CreateCostCenterUseCase: Instantiated use case.
    """
    return CreateCostCenterUseCase(repository=repo)


def get_set_budget_target_use_case(
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
) -> SetBudgetTargetUseCase:
    """Provide SetBudgetTargetUseCase.

    Args:
        budget_repo: Injected budget repository.
        cc_repo: Injected cost center repository.

    Returns:
        SetBudgetTargetUseCase: Instantiated use case.
    """
    return SetBudgetTargetUseCase(
        budget_repository=budget_repo,
        cost_center_repository=cc_repo,
    )


def get_get_hierarchy_budget_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
) -> GetHierarchyBudgetUseCase:
    """Provide GetHierarchyBudgetUseCase.

    Args:
        cc_repo: Injected cost center repository.
        budget_repo: Injected budget repository.

    Returns:
        GetHierarchyBudgetUseCase: Instantiated use case.
    """
    return GetHierarchyBudgetUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
    )


# --- Dependency Type Aliases ---

CreateCostCenterUseCaseDep = Annotated[
    CreateCostCenterUseCase, Depends(get_create_cost_center_use_case)
]
SetBudgetTargetUseCaseDep = Annotated[
    SetBudgetTargetUseCase, Depends(get_set_budget_target_use_case)
]
GetHierarchyBudgetUseCaseDep = Annotated[
    GetHierarchyBudgetUseCase, Depends(get_get_hierarchy_budget_use_case)
]
CostCenterRepoDep = Annotated[CostCenterRepository, Depends(get_cost_center_repository)]

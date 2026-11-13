"""Strategic indicators dependency providers and type annotations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)
from src.allocation.domain.repositories.measurement_repository import (
    MeasurementRepository,
)
from src.budgeting.domain.repositories.budget_repository import BudgetRepository
from src.budgeting.domain.repositories.cost_center_repository import (
    CostCenterRepository,
)
from src.indicators.application.use_cases.queries import (
    ComputePeriodIndicatorsUseCase,
    GenerateMaterialImpactReportUseCase,
    SimulateScenarioUseCase,
)

from .allocation import (
    get_accounting_account_repository,
    get_measurement_repository,
)
from .budgeting import (
    get_budget_repository,
    get_cost_center_repository,
)


def get_compute_period_indicators_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ComputePeriodIndicatorsUseCase:
    """Provide ComputePeriodIndicatorsUseCase.

    Args:
        cc_repo: Cost center repository.
        budget_repo: Budget repository.
        measurement_repo: Measurement repository.

    Returns:
        ComputePeriodIndicatorsUseCase: Instantiated use case.
    """
    return ComputePeriodIndicatorsUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )


def get_simulate_scenario_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> SimulateScenarioUseCase:
    """Provide SimulateScenarioUseCase.

    Args:
        cc_repo: Cost center repository.
        budget_repo: Budget repository.
        measurement_repo: Measurement repository.

    Returns:
        SimulateScenarioUseCase: Instantiated use case.
    """
    return SimulateScenarioUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
    )


def get_material_impact_use_case(
    cc_repo: Annotated[CostCenterRepository, Depends(get_cost_center_repository)],
    budget_repo: Annotated[BudgetRepository, Depends(get_budget_repository)],
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
    accounting_account_repo: Annotated[
        AccountingAccountRepository, Depends(get_accounting_account_repository)
    ],
) -> GenerateMaterialImpactReportUseCase:
    """Provide GenerateMaterialImpactReportUseCase.

    Args:
        cc_repo: Cost center repository.
        budget_repo: Budget repository.
        measurement_repo: Measurement repository.
        accounting_account_repo: Accounting account repository.

    Returns:
        GenerateMaterialImpactReportUseCase: Instantiated use case.
    """
    return GenerateMaterialImpactReportUseCase(
        cost_center_repository=cc_repo,
        budget_repository=budget_repo,
        measurement_repository=measurement_repo,
        accounting_account_repository=accounting_account_repo,
    )


# --- Dependency Type Aliases ---

ComputePeriodIndicatorsUseCaseDep = Annotated[
    ComputePeriodIndicatorsUseCase,
    Depends(get_compute_period_indicators_use_case),
]
SimulateScenarioUseCaseDep = Annotated[
    SimulateScenarioUseCase, Depends(get_simulate_scenario_use_case)
]
MaterialImpactUseCaseDep = Annotated[
    GenerateMaterialImpactReportUseCase,
    Depends(get_material_impact_use_case),
]

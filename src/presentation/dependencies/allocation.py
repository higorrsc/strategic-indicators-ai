"""Cost allocation dependency providers and type annotations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.allocation.application.use_cases.commands import (
    ApproveMeasurementUseCase,
    RegisterAccountingAccountUseCase,
    RegisterContractUseCase,
    SubmitMeasurementUseCase,
)
from src.allocation.application.use_cases.queries import (
    GetCostCenterAccountingBreakdownUseCase,
    ListAccountingAccountsUseCase,
    ListContractsUseCase,
    ListMeasurementsUseCase,
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
from src.allocation.domain.repositories.supplier_repository import (
    SupplierRepository,
)
from src.allocation.infrastructure.repositories import (
    SqlAlchemyAccountingAccountRepository,
    SqlAlchemyContractRepository,
    SqlAlchemyMeasurementRepository,
    SqlAlchemySupplierRepository,
)

from .container import DependencyContainer, get_container
from .database import get_db_session


def get_supplier_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> SupplierRepository:
    """Provide supplier repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        SupplierRepository: Supplier repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemySupplierRepository(session)
    return container.supplier_repo


def get_contract_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> ContractRepository:
    """Provide contract repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        ContractRepository: Contract repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyContractRepository(session)
    return container.contract_repo


def get_measurement_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> MeasurementRepository:
    """Provide measurement repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        MeasurementRepository: Measurement repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyMeasurementRepository(session)
    return container.measurement_repo


def get_accounting_account_repository(
    container: Annotated[DependencyContainer, Depends(get_container)],
    session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> AccountingAccountRepository:
    """Provide accounting account repository.

    Args:
        container: Dependency container.
        session: Optional active request session.

    Returns:
        AccountingAccountRepository: Accounting account repository.
    """
    if container.use_database and session is not None:
        return SqlAlchemyAccountingAccountRepository(session)
    return container.accounting_account_repo


def get_register_contract_use_case(
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
    supplier_repo: Annotated[SupplierRepository, Depends(get_supplier_repository)],
) -> RegisterContractUseCase:
    """Provide RegisterContractUseCase.

    Args:
        contract_repo: Injected contract repository.
        supplier_repo: Injected supplier repository.

    Returns:
        RegisterContractUseCase: Instantiated use case.
    """
    return RegisterContractUseCase(
        contract_repository=contract_repo,
        supplier_repository=supplier_repo,
    )


def get_submit_measurement_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
    accounting_account_repo: Annotated[
        AccountingAccountRepository, Depends(get_accounting_account_repository)
    ],
) -> SubmitMeasurementUseCase:
    """Provide SubmitMeasurementUseCase.

    Args:
        measurement_repo: Injected measurement repository.
        contract_repo: Injected contract repository.
        accounting_account_repo: Injected accounting account repository.

    Returns:
        SubmitMeasurementUseCase: Instantiated use case.
    """
    return SubmitMeasurementUseCase(
        measurement_repository=measurement_repo,
        contract_repository=contract_repo,
        accounting_account_repository=accounting_account_repo,
    )


def get_register_accounting_account_use_case(
    repo: Annotated[
        AccountingAccountRepository, Depends(get_accounting_account_repository)
    ],
) -> RegisterAccountingAccountUseCase:
    """Provide RegisterAccountingAccountUseCase.

    Args:
        repo: Injected accounting account repository.

    Returns:
        RegisterAccountingAccountUseCase: Instantiated use case.
    """
    return RegisterAccountingAccountUseCase(accounting_account_repository=repo)


def get_list_accounting_accounts_use_case(
    repo: Annotated[
        AccountingAccountRepository, Depends(get_accounting_account_repository)
    ],
) -> ListAccountingAccountsUseCase:
    """Provide ListAccountingAccountsUseCase.

    Args:
        repo: Injected accounting account repository.

    Returns:
        ListAccountingAccountsUseCase: Instantiated use case.
    """
    return ListAccountingAccountsUseCase(accounting_account_repository=repo)


def get_cost_center_accounting_breakdown_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
    accounting_account_repo: Annotated[
        AccountingAccountRepository, Depends(get_accounting_account_repository)
    ],
) -> GetCostCenterAccountingBreakdownUseCase:
    """Provide GetCostCenterAccountingBreakdownUseCase.

    Args:
        measurement_repo: Injected measurement repository.
        accounting_account_repo: Injected accounting account repository.

    Returns:
        GetCostCenterAccountingBreakdownUseCase: Instantiated use case.
    """
    return GetCostCenterAccountingBreakdownUseCase(
        measurement_repository=measurement_repo,
        accounting_account_repository=accounting_account_repo,
    )


def get_approve_measurement_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ApproveMeasurementUseCase:
    """Provide ApproveMeasurementUseCase.

    Args:
        measurement_repo: Injected measurement repository.

    Returns:
        ApproveMeasurementUseCase: Instantiated use case.
    """
    return ApproveMeasurementUseCase(
        measurement_repository=measurement_repo,
    )


def get_list_contracts_use_case(
    contract_repo: Annotated[ContractRepository, Depends(get_contract_repository)],
) -> ListContractsUseCase:
    """Provide ListContractsUseCase.

    Args:
        contract_repo: Injected contract repository.

    Returns:
        ListContractsUseCase: Instantiated use case.
    """
    return ListContractsUseCase(contract_repository=contract_repo)


def get_list_measurements_use_case(
    measurement_repo: Annotated[
        MeasurementRepository, Depends(get_measurement_repository)
    ],
) -> ListMeasurementsUseCase:
    """Provide ListMeasurementsUseCase.

    Args:
        measurement_repo: Injected measurement repository.

    Returns:
        ListMeasurementsUseCase: Instantiated use case.
    """
    return ListMeasurementsUseCase(measurement_repository=measurement_repo)


# --- Dependency Type Aliases ---

RegisterContractUseCaseDep = Annotated[
    RegisterContractUseCase, Depends(get_register_contract_use_case)
]
SubmitMeasurementUseCaseDep = Annotated[
    SubmitMeasurementUseCase, Depends(get_submit_measurement_use_case)
]
ApproveMeasurementUseCaseDep = Annotated[
    ApproveMeasurementUseCase, Depends(get_approve_measurement_use_case)
]
ListContractsUseCaseDep = Annotated[
    ListContractsUseCase, Depends(get_list_contracts_use_case)
]
ListMeasurementsUseCaseDep = Annotated[
    ListMeasurementsUseCase, Depends(get_list_measurements_use_case)
]
SupplierRepoDep = Annotated[SupplierRepository, Depends(get_supplier_repository)]
ContractRepoDep = Annotated[ContractRepository, Depends(get_contract_repository)]
MeasurementRepoDep = Annotated[
    MeasurementRepository, Depends(get_measurement_repository)
]
AccountingAccountRepoDep = Annotated[
    AccountingAccountRepository, Depends(get_accounting_account_repository)
]
RegisterAccountingAccountUseCaseDep = Annotated[
    RegisterAccountingAccountUseCase,
    Depends(get_register_accounting_account_use_case),
]
ListAccountingAccountsUseCaseDep = Annotated[
    ListAccountingAccountsUseCase,
    Depends(get_list_accounting_accounts_use_case),
]
GetCostCenterAccountingBreakdownUseCaseDep = Annotated[
    GetCostCenterAccountingBreakdownUseCase,
    Depends(get_cost_center_accounting_breakdown_use_case),
]

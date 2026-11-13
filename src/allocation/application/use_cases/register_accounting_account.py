"""Use case for registering a new accounting account."""

from src.allocation.application.dto import (
    AccountingAccountDTO,
    RegisterAccountingAccountCommand,
)
from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.exceptions import DuplicateAccountCodeError
from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)
from src.shared.domain.value_objects import AccountCode


class RegisterAccountingAccountUseCase:
    """Orchestrates registering a new accounting account."""

    def __init__(
        self,
        accounting_account_repository: AccountingAccountRepository,
    ) -> None:
        """Initialize use case with repository.

        Args:
            accounting_account_repository: Repository for persistence.
        """
        self._accounting_account_repository = accounting_account_repository

    async def execute(
        self, command: RegisterAccountingAccountCommand
    ) -> AccountingAccountDTO:
        """Register a new accounting account ensuring code uniqueness.

        Args:
            command: Registration command.

        Returns:
            AccountingAccountDTO: The created accounting account representation.
        """
        code = AccountCode(command.code)
        existing = await self._accounting_account_repository.get_by_code(code)
        if existing is not None:
            raise DuplicateAccountCodeError(
                f"Accounting account with code '{command.code}' already exists."
            )

        account = AccountingAccount(
            code=code,
            name=command.name,
            description=command.description,
        )
        await self._accounting_account_repository.save(account)

        return AccountingAccountDTO(
            id=account.id,
            code=str(account.code),
            name=account.name,
            description=account.description,
            is_active=account.is_active,
        )

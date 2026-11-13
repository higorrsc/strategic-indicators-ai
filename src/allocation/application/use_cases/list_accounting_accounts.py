"""Use case for listing accounting accounts with pagination."""

from src.allocation.application.dto import (
    AccountingAccountDTO,
    ListAccountingAccountsQuery,
    PaginatedResultDTO,
)
from src.allocation.domain.repositories.accounting_account_repository import (
    AccountingAccountRepository,
)


class ListAccountingAccountsUseCase:
    """Orchestrates paginated listing of accounting accounts."""

    def __init__(
        self,
        accounting_account_repository: AccountingAccountRepository,
    ) -> None:
        """Initialize use case with repository.

        Args:
            accounting_account_repository: Repository for querying accounts.
        """
        self._accounting_account_repository = accounting_account_repository

    async def execute(
        self, query: ListAccountingAccountsQuery
    ) -> PaginatedResultDTO[AccountingAccountDTO]:
        """Query accounting accounts with pagination and filtering.

        Args:
            query: Query parameters including page, per_page, and active_only.

        Returns:
            PaginatedResultDTO[AccountingAccountDTO]: Paginated result envelope.
        """
        page = max(1, query.page)
        per_page = max(1, query.per_page)
        offset = (page - 1) * per_page

        total_items = await self._accounting_account_repository.count(
            active_only=query.active_only
        )
        accounts = await self._accounting_account_repository.list_all(
            active_only=query.active_only,
            offset=offset,
            limit=per_page,
        )

        dtos = [
            AccountingAccountDTO(
                id=a.id,
                code=str(a.code),
                name=a.name,
                description=a.description,
                is_active=a.is_active,
            )
            for a in accounts
        ]

        return PaginatedResultDTO(
            items=dtos,
            total_items=total_items,
            page=page,
            per_page=per_page,
        )

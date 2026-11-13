import pytest

from src.allocation.application.dto import (
    ListAccountingAccountsQuery,
    RegisterAccountingAccountCommand,
)
from src.allocation.application.use_cases.commands import (
    RegisterAccountingAccountUseCase,
)
from src.allocation.application.use_cases.queries import (
    ListAccountingAccountsUseCase,
)
from src.allocation.infrastructure.repositories import (
    InMemoryAccountingAccountRepository,
)


@pytest.mark.asyncio
async def test_should_list_accounting_accounts_with_pagination() -> None:
    repo = InMemoryAccountingAccountRepository()
    reg_use_case = RegisterAccountingAccountUseCase(repo)
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.1", name="Cat 1")
    )
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.2", name="Cat 2")
    )
    await reg_use_case.execute(
        RegisterAccountingAccountCommand(code="3.3", name="Cat 3")
    )

    list_use_case = ListAccountingAccountsUseCase(repo)
    page1 = await list_use_case.execute(ListAccountingAccountsQuery(page=1, per_page=2))

    assert page1.total_items == 3
    assert len(page1.items) == 2
    assert page1.items[0].code == "3.1"
    assert page1.items[1].code == "3.2"

    page2 = await list_use_case.execute(ListAccountingAccountsQuery(page=2, per_page=2))
    assert page2.total_items == 3
    assert len(page2.items) == 1
    assert page2.items[0].code == "3.3"

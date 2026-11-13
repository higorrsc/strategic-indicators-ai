import pytest

from src.allocation.application.dto import RegisterAccountingAccountCommand
from src.allocation.application.use_cases.commands import (
    RegisterAccountingAccountUseCase,
)
from src.allocation.domain.exceptions import DuplicateAccountCodeError
from src.allocation.infrastructure.repositories import (
    InMemoryAccountingAccountRepository,
)
from src.shared.domain.exceptions import InvalidAccountCodeError
from src.shared.domain.value_objects import AccountCode


@pytest.mark.asyncio
async def test_should_register_accounting_account_successfully() -> None:
    repo = InMemoryAccountingAccountRepository()
    use_case = RegisterAccountingAccountUseCase(repo)
    command = RegisterAccountingAccountCommand(
        code="3.1.01",
        name="Software Licenses",
        description="SaaS tools",
    )

    dto = await use_case.execute(command)

    assert dto.code == "3.1.01"
    assert dto.name == "Software Licenses"
    assert dto.description == "SaaS tools"
    assert dto.is_active is True

    stored = await repo.get_by_id(dto.id)
    assert stored is not None
    assert stored.code == AccountCode("3.1.01")


@pytest.mark.asyncio
async def test_should_reject_duplicate_accounting_account_code() -> None:
    repo = InMemoryAccountingAccountRepository()
    use_case = RegisterAccountingAccountUseCase(repo)
    command = RegisterAccountingAccountCommand(code="3.1.01", name="Licenses")
    await use_case.execute(command)

    with pytest.raises(DuplicateAccountCodeError):
        await use_case.execute(command)


@pytest.mark.asyncio
async def test_should_reject_invalid_accounting_account_code() -> None:
    repo = InMemoryAccountingAccountRepository()
    use_case = RegisterAccountingAccountUseCase(repo)
    command = RegisterAccountingAccountCommand(code="invalid..code", name="Bad")

    with pytest.raises(InvalidAccountCodeError):
        await use_case.execute(command)

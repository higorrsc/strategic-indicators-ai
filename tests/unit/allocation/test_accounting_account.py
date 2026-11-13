"""Unit tests for AccountingAccount domain entity."""

from uuid import uuid4

import pytest

from src.allocation.domain.entities.accounting_account import AccountingAccount
from src.allocation.domain.entities.measurement import AllocationEntry
from src.allocation.domain.exceptions import AllocationDomainError
from src.shared.domain.value_objects import AccountCode, Money, Percentage


def test_should_create_valid_accounting_account() -> None:
    code = AccountCode("3.1.01")
    account = AccountingAccount(
        code=code,
        name="Software Licenses",
        description="SaaS & cloud licenses",
    )

    assert account.code == code
    assert account.name == "Software Licenses"
    assert account.description == "SaaS & cloud licenses"
    assert account.is_active is True
    assert account.id is not None


def test_should_reject_empty_accounting_account_name() -> None:
    with pytest.raises(AllocationDomainError, match="name cannot be empty"):
        AccountingAccount(code=AccountCode("3.1"), name="   ")


def test_should_activate_and_deactivate_accounting_account() -> None:
    account = AccountingAccount(code=AccountCode("3.1"), name="Cloud Services")
    assert account.is_active is True

    account.deactivate()
    assert not account.is_active

    account.activate()
    assert account.is_active


def test_should_update_accounting_account_details() -> None:
    account = AccountingAccount(code=AccountCode("3.1"), name="Old Name")
    account.update_details("New Name", "New Description")

    assert account.name == "New Name"
    assert account.description == "New Description"


def test_should_reject_empty_name_on_update() -> None:
    account = AccountingAccount(code=AccountCode("3.1"), name="Old Name")
    with pytest.raises(AllocationDomainError, match="name cannot be empty"):
        account.update_details("  ", "desc")


def test_should_instantiate_allocation_entry_with_accounting_account_id() -> None:
    cc_id = uuid4()
    account_id = uuid4()
    entry = AllocationEntry(
        cost_center_id=cc_id,
        amount=Money.from_float_or_int(1000, "BRL"),
        percentage=Percentage.from_number(100),
        accounting_account_id=account_id,
    )

    assert entry.cost_center_id == cc_id
    assert entry.accounting_account_id == account_id
    assert entry.amount.amount == 1000.00

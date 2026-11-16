"""Pure REST tests: contract (schema), business rules and negative cases. No browser -> fast feedback."""
from decimal import Decimal

import allure
import pytest

from api.base_client import ApiError
from config.config import Config

pytestmark = [pytest.mark.api, allure.feature("Accounts API")]

MIN_DEPOSIT = Decimal(Config.NEW_ACCOUNT_MIN_DEPOSIT)


@pytest.mark.smoke
@allure.title("New customer profile and default account match the API contract")
def test_new_customer_contract(api, customer):
    # Parsing into Pydantic models already validates field names/types (extra='forbid')
    profile = api.get_customer(customer.id)
    assert profile.first_name == customer.data.first_name
    assert profile.address.city == customer.data.city

    accounts = api.get_accounts(customer.id)
    assert [a.type for a in accounts] == ["CHECKING"]
    assert accounts[0].customer_id == customer.id
    assert accounts[0].balance > 0


@pytest.mark.regression
@pytest.mark.parametrize("account_type", ["CHECKING", "SAVINGS"])
@allure.title("Opening an account moves exactly the minimum deposit from the funding account")
def test_open_account_moves_min_deposit(api, customer, account_type):
    source = customer.primary_account
    before = api.balance(source.id)

    new = api.create_account(customer.id, account_type, source.id)

    assert new.type == account_type
    assert api.balance(new.id) == MIN_DEPOSIT
    assert api.balance(source.id) == before - MIN_DEPOSIT


@pytest.mark.smoke
@pytest.mark.parametrize("amount", ["0.01", "25.50", "100.00"], ids=["one_cent", "decimal", "round"])
@allure.title("Internal transfer conserves the customer's total balance")
def test_transfer_conserves_total_balance(api, customer, second_account, amount):
    amount = Decimal(amount)
    src, dst = customer.primary_account.id, second_account.id
    total_before = api.total_balance(customer.id)
    src_before, dst_before = api.balance(src), api.balance(dst)

    api.transfer(src, dst, amount)

    assert api.balance(src) == src_before - amount
    assert api.balance(dst) == dst_before + amount
    assert api.total_balance(customer.id) == total_before, "Money was created or destroyed"


@pytest.mark.regression
@allure.title("Transfer writes a matching Debit and Credit to the ledger")
def test_transfer_writes_double_entry(api, customer, second_account):
    amount = Decimal("42.42")
    src, dst = customer.primary_account.id, second_account.id
    src_known, dst_known = api.transaction_ids(src), api.transaction_ids(dst)

    api.transfer(src, dst, amount)

    debits = api.new_transactions(src, src_known)
    credits = api.new_transactions(dst, dst_known)
    assert [(t.type, t.amount, t.description) for t in debits] == [("Debit", amount, "Funds Transfer Sent")]
    assert [(t.type, t.amount, t.description) for t in credits] == [("Credit", amount, "Funds Transfer Received")]
    assert api.find_transactions_by_amount(src, amount) == debits  # search-by-amount endpoint agrees


@pytest.mark.regression
@pytest.mark.parametrize("path, status", [
    ("accounts/999999999", 400),
    ("accounts/abc", 404),
    ("customers/999999999", 400),
], ids=["unknown_account", "non_numeric_id", "unknown_customer"])
@allure.title("Invalid identifiers are rejected")
def test_invalid_ids_rejected(api, path, status):
    assert api.get(path, expected_status=None).status_code == status


@pytest.mark.regression
@allure.title("Login with wrong password is rejected")
def test_login_wrong_password(api, customer):
    with pytest.raises(ApiError, match="400"):
        api.login(customer.data.username, "wrong-password")


@pytest.mark.regression
@pytest.mark.xfail(strict=True, reason="DEFECT PB-101: transfer API accepts negative amounts and "
                                       "moves money in the reverse direction")
@allure.title("Transfer with a negative amount is rejected")
def test_negative_transfer_rejected(api, customer, second_account):
    src, dst = customer.primary_account.id, second_account.id
    dst_before = api.balance(dst)

    resp = api.post("transfer", expected_status=None,
                    params={"fromAccountId": src, "toAccountId": dst, "amount": "-5"})

    assert resp.status_code == 400
    assert api.balance(dst) == dst_before

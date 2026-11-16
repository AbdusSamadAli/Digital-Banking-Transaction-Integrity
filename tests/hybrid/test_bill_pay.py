from decimal import Decimal

import allure
import pytest

from utils.data_factory import PayeeData

pytestmark = [pytest.mark.hybrid, allure.feature("Bill Pay")]


@pytest.mark.smoke
@allure.title("Bill paid in the UI debits the account and is recorded in the ledger")
def test_bill_pay_debits_account(bank_ui, api, customer):
    src = customer.primary_account.id
    before, known = api.balance(src), api.transaction_ids(src)
    payee, amount = PayeeData(), Decimal("63.19")

    receipt = bank_ui.menu.bill_pay().pay(payee, amount, src).confirmation()
    assert receipt == {"payee": payee.name, "amount": amount, "from": src}

    with allure.step("Verify debit via API"):
        assert api.balance(src) == before - amount
        assert [(t.type, t.amount, t.description) for t in api.new_transactions(src, known)] == \
            [("Debit", amount, f"Bill Payment to {payee.name}")]


@pytest.mark.regression
@pytest.mark.parametrize("override, error_id, message", [
    ({"verify_account": "00000"}, "verifyAccount-mismatch", "The account numbers do not match."),
    ({"amount": ""}, "amount-empty", "The amount cannot be empty."),
    ({"amount": "abc"}, "amount-invalid", "Please enter a valid amount."),
], ids=["account_mismatch", "empty_amount", "non_numeric_amount"])
@allure.title("Invalid bill payment is blocked and no money moves")
def test_bill_pay_validation(bank_ui, api, customer, override, error_id, message):
    src = customer.primary_account.id
    before = api.balance(src)
    amount = override.get("amount", "10.00")

    page = bank_ui.menu.bill_pay().pay(PayeeData(), amount, src,
                                       verify_account=override.get("verify_account"))

    assert page.error_text(error_id) == message
    assert not page.is_result_shown()
    assert api.balance(src) == before

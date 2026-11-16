"""The core of the suite: the UI says "Transfer Complete!" - but did the ledger actually move?"""
from decimal import Decimal

import allure
import pytest

pytestmark = [pytest.mark.hybrid, allure.feature("Funds Transfer")]


@pytest.mark.smoke
@pytest.mark.parametrize("amount", ["0.01", "37.25", "100"], ids=["one_cent", "decimal", "whole"])
@allure.title("UI transfer updates both balances and writes Debit/Credit entries")
def test_transfer_via_ui_updates_ledger(bank_ui, api, customer, second_account, amount):
    amount = Decimal(amount)
    src, dst = customer.primary_account.id, second_account.id
    src_before, dst_before = api.balance(src), api.balance(dst)
    total_before = api.total_balance(customer.id)
    # Snapshot the ledger: opening second_account already wrote a $100 debit, so searching by
    # amount alone would be ambiguous. Assert only on entries this transfer created.
    src_known, dst_known = api.transaction_ids(src), api.transaction_ids(dst)

    receipt = bank_ui.menu.transfer_funds().transfer(amount, src, dst).confirmation()
    assert receipt == {"amount": amount, "from": src, "to": dst}, "UI confirmation shows wrong details"

    with allure.step("Verify balances via API"):
        assert api.balance(src) == src_before - amount
        assert api.balance(dst) == dst_before + amount
        assert api.total_balance(customer.id) == total_before

    with allure.step("Verify double-entry ledger via API"):
        assert [(t.type, t.amount) for t in api.new_transactions(src, src_known)] == [("Debit", amount)]
        assert [(t.type, t.amount) for t in api.new_transactions(dst, dst_known)] == [("Credit", amount)]


@pytest.mark.regression
@allure.title("Overdrawing transfer: what the UI promises vs. what the ledger shows")
def test_transfer_more_than_balance(bank_ui, api, customer, second_account):
    """ParaBank allows overdrafts. We don't assert a business rule we don't own;
    we assert consistency: whatever the UI reports must match the backend exactly."""
    src, dst = customer.primary_account.id, second_account.id
    src_before = api.balance(src)
    amount = src_before + Decimal("1000.00")

    page = bank_ui.menu.transfer_funds().transfer(amount, src, dst)

    if page.is_success_shown():
        assert api.balance(src) == src_before - amount
    else:
        assert page.is_error_shown()
        assert api.balance(src) == src_before, "UI showed an error but money still moved"


@pytest.mark.regression
@allure.title("Transfer form blocks an empty amount and moves no money")
def test_transfer_empty_amount(bank_ui, api, customer, second_account):
    src, dst = customer.primary_account.id, second_account.id
    src_before = api.balance(src)

    page = bank_ui.menu.transfer_funds().transfer("", src, dst)

    assert not page.is_success_shown(timeout=3)
    assert api.balance(src) == src_before

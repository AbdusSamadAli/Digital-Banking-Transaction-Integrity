"""Reverse direction: seed state through the API, then check the UI renders it faithfully."""
from decimal import Decimal

import allure
import pytest

pytestmark = [pytest.mark.hybrid, allure.feature("Accounts Overview")]


@pytest.mark.smoke
@allure.title("Overview shows every account with the backend balance and a correct total")
def test_overview_matches_backend(bank_ui, api, customer):
    with allure.step("Seed: two extra accounts + a transfer, all via API"):
        checking = api.create_account(customer.id, "CHECKING", customer.primary_account.id)
        savings = api.create_account(customer.id, "SAVINGS", customer.primary_account.id)
        api.transfer(customer.primary_account.id, savings.id, Decimal("12.34"))

    overview = bank_ui.open()  # reload so the page renders the seeded state
    expected = {a.id: a.balance for a in api.get_accounts(customer.id)}
    assert set(expected) == {customer.primary_account.id, checking.id, savings.id}
    assert overview.balances() == expected
    assert overview.total() == sum(expected.values(), Decimal("0"))

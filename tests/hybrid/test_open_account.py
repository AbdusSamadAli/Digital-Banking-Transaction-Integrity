from decimal import Decimal

import allure
import pytest

from config.config import Config

pytestmark = [pytest.mark.hybrid, allure.feature("Open Account")]


@pytest.mark.smoke
@pytest.mark.parametrize("account_type", ["CHECKING", "SAVINGS"])
@allure.title("Account opened in the UI exists in the backend with the minimum deposit")
def test_open_account_via_ui(bank_ui, api, customer, account_type):
    source_id = customer.primary_account.id
    source_before = api.balance(source_id)

    new_id = bank_ui.menu.open_new_account().open_account(account_type, source_id)

    with allure.step("Verify new account and funding debit via API"):
        new = api.get_account(new_id)
        assert new.customer_id == customer.id
        assert new.type == account_type
        assert new.balance == Decimal(Config.NEW_ACCOUNT_MIN_DEPOSIT)
        assert api.balance(source_id) == source_before - Decimal(Config.NEW_ACCOUNT_MIN_DEPOSIT)
        assert {a.id for a in api.get_accounts(customer.id)} == {source_id, new_id}

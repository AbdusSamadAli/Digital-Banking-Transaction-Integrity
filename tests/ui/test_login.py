import allure
import pytest

from pages.login_page import LoginPage

pytestmark = [pytest.mark.ui, allure.feature("Authentication")]


@pytest.mark.smoke
@allure.title("Customer can log in through the UI and log out")
def test_login_and_logout(driver, customer):
    overview = LoginPage(driver).open().login(customer.data.username, customer.data.password)

    assert overview.is_loaded()
    assert overview.menu.welcome_text() == f"Welcome {customer.data.first_name} {customer.data.last_name}"

    login = overview.menu.log_out()
    assert login.is_displayed()


@pytest.mark.regression
@pytest.mark.parametrize("username, password", [
    ("valid", "wrong-password"),
    ("no_such_user_9f3k", "whatever"),
], ids=["wrong_password", "unknown_user"])
@allure.title("Invalid credentials are rejected")
def test_invalid_login(driver, customer, username, password):
    username = customer.data.username if username == "valid" else username
    page = LoginPage(driver).open()
    page.login(username, password)
    assert page.error_message() == "The username and password could not be verified."


@pytest.mark.regression
@allure.title("Login with empty fields is rejected")
def test_empty_login(driver):
    page = LoginPage(driver).open()
    page.login("", "")
    assert page.error_message() == "Please enter a username and password."

import allure
import pytest

from pages.register_page import RegisterPage
from utils.data_factory import CustomerData

pytestmark = allure.feature("Customer Registration")


@pytest.mark.smoke
@pytest.mark.hybrid
@allure.title("Customer registered in the UI is persisted correctly in the backend")
def test_ui_registration_persists_customer(driver, api):
    data = CustomerData()
    page = RegisterPage(driver).open().register(data)

    assert page.title() == f"Welcome {data.username}"
    assert "created successfully" in page.success_message()

    with allure.step("Verify via API that every field was stored as entered"):
        profile = api.login(data.username, data.password)
        assert (profile.first_name, profile.last_name) == (data.first_name, data.last_name)
        assert profile.address.street == data.street
        assert profile.address.zip_code == data.zip_code
        assert profile.phone_number == data.phone
        accounts = api.get_accounts(profile.id)
        assert len(accounts) == 1 and accounts[0].type == "CHECKING"


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("override, field_id, message", [
    ({"first_name": ""}, "customer.firstName", "First name is required."),
    ({"last_name": ""}, "customer.lastName", "Last name is required."),
    ({"ssn": ""}, "customer.ssn", "Social Security Number is required."),
    ({"username": ""}, "customer.username", "Username is required."),
], ids=["no_first_name", "no_last_name", "no_ssn", "no_username"])
@allure.title("Required registration fields are validated")
def test_required_fields(driver, override, field_id, message):
    data = CustomerData(**override)
    page = RegisterPage(driver).open().register(data)
    assert page.field_error(field_id) == message


@pytest.mark.ui
@pytest.mark.regression
@allure.title("Password confirmation must match")
def test_password_mismatch(driver):
    page = RegisterPage(driver).open().register(CustomerData(), confirm_password="different123")
    assert page.field_error("repeatedPassword") == "Passwords did not match."


@pytest.mark.hybrid
@pytest.mark.regression
@allure.title("Duplicate username is rejected")
def test_duplicate_username(driver, customer):
    page = RegisterPage(driver).open().register(CustomerData(username=customer.data.username))
    assert page.field_error("customer.username") == "This username already exists."

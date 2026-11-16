import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.data_factory import CustomerData


class RegisterPage(BasePage):
    path = "/register.htm"

    SUBMIT = (By.CSS_SELECTOR, "#customerForm input[value='Register']")
    TITLE = (By.CSS_SELECTOR, "#rightPanel h1.title")
    SUCCESS_MSG = (By.CSS_SELECTOR, "#rightPanel p")

    @allure.step("Fill and submit registration form")
    def register(self, data: CustomerData, confirm_password: str | None = None):
        for field_id, value in data.as_form(confirm_password).items():
            self.type((By.ID, field_id), value)
        self.click(self.SUBMIT)
        return self

    def title(self) -> str:
        return self.text_of(self.TITLE)

    def success_message(self) -> str:
        return self.text_of(self.SUCCESS_MSG)

    def field_error(self, field_id: str) -> str:
        """Server-side validation message rendered next to a field, e.g. 'customer.firstName'."""
        return self.text_of((By.ID, f"{field_id}.errors"))

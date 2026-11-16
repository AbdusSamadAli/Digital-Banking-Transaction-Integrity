import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.data_factory import PayeeData
from utils.money import parse_money


class BillPayPage(BasePage):
    path = "/billpay.htm"

    FROM_ACCOUNT = (By.CSS_SELECTOR, "select[name='fromAccountId']")
    SUBMIT = (By.CSS_SELECTOR, "#billpayForm input[value='Send Payment']")
    RESULT_TITLE = (By.CSS_SELECTOR, "#billpayResult h1.title")
    # The result panel reuses id="amount"/"fromAccountId", so scope locators to the panel
    RESULT_PAYEE = (By.CSS_SELECTOR, "#billpayResult #payeeName")
    RESULT_AMOUNT = (By.CSS_SELECTOR, "#billpayResult #amount")
    RESULT_FROM = (By.CSS_SELECTOR, "#billpayResult #fromAccountId")

    @staticmethod
    def _field(name: str):
        return (By.CSS_SELECTOR, f"#billpayForm input[name='{name}']")

    @staticmethod
    def validation_error(error_id: str):
        return (By.ID, f"validationModel-{error_id}")

    @allure.step("Pay {amount} to payee from #{from_account_id}")
    def pay(self, payee: PayeeData, amount, from_account_id: int, verify_account: str | None = None):
        fields = {
            "payee.name": payee.name,
            "payee.address.street": payee.street,
            "payee.address.city": payee.city,
            "payee.address.state": payee.state,
            "payee.address.zipCode": payee.zip_code,
            "payee.phoneNumber": payee.phone,
            "payee.accountNumber": payee.account_number,
            "verifyAccount": payee.account_number if verify_account is None else verify_account,
            "amount": str(amount),
        }
        for name, value in fields.items():
            self.type(self._field(name), value)
        self.select_by_value(self.FROM_ACCOUNT, str(from_account_id))
        self.click(self.SUBMIT)
        return self

    def confirmation(self) -> dict:
        self.wait_for_text(self.RESULT_TITLE, "Bill Payment Complete")
        return {
            "payee": self.text_of(self.RESULT_PAYEE),
            "amount": parse_money(self.text_of(self.RESULT_AMOUNT)),
            "from": int(self.text_of(self.RESULT_FROM)),
        }

    def error_text(self, error_id: str) -> str:
        return self.text_of(self.validation_error(error_id))

    def is_result_shown(self, timeout: int = 3) -> bool:
        return self.is_visible(self.RESULT_TITLE, timeout)

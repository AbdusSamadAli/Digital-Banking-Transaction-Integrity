import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.money import parse_money


class TransferPage(BasePage):
    path = "/transfer.htm"

    AMOUNT = (By.ID, "amount")
    FROM_ACCOUNT = (By.CSS_SELECTOR, "#fromAccountId")
    TO_ACCOUNT = (By.CSS_SELECTOR, "#toAccountId")
    SUBMIT = (By.CSS_SELECTOR, "#transferForm input[value='Transfer']")
    RESULT_TITLE = (By.CSS_SELECTOR, "#showResult h1.title")
    RESULT_AMOUNT = (By.ID, "amountResult")
    RESULT_FROM = (By.ID, "fromAccountIdResult")
    RESULT_TO = (By.ID, "toAccountIdResult")
    ERROR_PANEL = (By.CSS_SELECTOR, "#showError")

    @allure.step("Transfer {amount} from #{from_account_id} to #{to_account_id}")
    def transfer(self, amount, from_account_id: int, to_account_id: int):
        self.select_by_value(self.FROM_ACCOUNT, str(from_account_id))
        self.select_by_value(self.TO_ACCOUNT, str(to_account_id))
        self.type(self.AMOUNT, str(amount))
        self.click(self.SUBMIT)
        return self

    def wait_for_success(self):
        self.wait_for_text(self.RESULT_TITLE, "Transfer Complete!")
        return self

    def confirmation(self) -> dict:
        self.wait_for_success()
        return {
            "amount": parse_money(self.text_of(self.RESULT_AMOUNT)),
            "from": int(self.text_of(self.RESULT_FROM)),
            "to": int(self.text_of(self.RESULT_TO)),
        }

    def is_success_shown(self, timeout: int = 5) -> bool:
        return self.is_visible(self.RESULT_TITLE, timeout)

    def is_error_shown(self, timeout: int = 5) -> bool:
        return self.is_visible(self.ERROR_PANEL, timeout)

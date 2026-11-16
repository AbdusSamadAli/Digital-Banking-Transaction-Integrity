import allure
from selenium.webdriver.common.by import By

from api.bank_api import ACCOUNT_TYPE_CODES
from pages.base_page import BasePage


class OpenAccountPage(BasePage):
    path = "/openaccount.htm"

    TYPE = (By.CSS_SELECTOR, "#type")
    FROM_ACCOUNT = (By.CSS_SELECTOR, "#fromAccountId")
    SUBMIT = (By.CSS_SELECTOR, "#openAccountForm input[value='Open New Account']")
    RESULT_TITLE = (By.CSS_SELECTOR, "#openAccountResult h1.title")
    NEW_ACCOUNT_ID = (By.ID, "newAccountId")

    @allure.step("Open a {account_type} account funded from #{from_account_id}")
    def open_account(self, account_type: str, from_account_id: int) -> int:
        self.select_by_value(self.TYPE, str(ACCOUNT_TYPE_CODES[account_type]))
        self.select_by_value(self.FROM_ACCOUNT, str(from_account_id))
        self.click(self.SUBMIT)
        self.wait_for_text(self.RESULT_TITLE, "Account Opened!")
        self.wait.until(lambda d: d.find_element(*self.NEW_ACCOUNT_ID).text.strip().isdigit())
        return int(self.text_of(self.NEW_ACCOUNT_ID))

"""Left-hand 'Account Services' menu, shown on every logged-in page. Modelled once as a component."""
import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class SideMenu(BasePage):
    PANEL = (By.ID, "leftPanel")
    WELCOME = (By.CSS_SELECTOR, "#leftPanel p.smallText")

    def _go(self, link_text: str):
        with allure.step(f"Menu -> {link_text}"):
            self.click((By.LINK_TEXT, link_text))

    def welcome_text(self) -> str:
        return self.text_of(self.WELCOME)

    def accounts_overview(self):
        from pages.accounts_overview_page import AccountsOverviewPage
        self._go("Accounts Overview")
        return AccountsOverviewPage(self.driver)

    def open_new_account(self):
        from pages.open_account_page import OpenAccountPage
        self._go("Open New Account")
        return OpenAccountPage(self.driver)

    def transfer_funds(self):
        from pages.transfer_page import TransferPage
        self._go("Transfer Funds")
        return TransferPage(self.driver)

    def bill_pay(self):
        from pages.bill_pay_page import BillPayPage
        self._go("Bill Pay")
        return BillPayPage(self.driver)

    def log_out(self):
        from pages.login_page import LoginPage
        self._go("Log Out")
        return LoginPage(self.driver)

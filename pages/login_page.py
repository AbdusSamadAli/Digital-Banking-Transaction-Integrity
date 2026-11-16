import allure
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/index.htm"

    USERNAME = (By.NAME, "username")
    PASSWORD = (By.NAME, "password")
    LOGIN_BTN = (By.CSS_SELECTOR, "input[value='Log In']")
    ERROR = (By.CSS_SELECTOR, "#rightPanel p.error")

    @allure.step("Log in as {username}")
    def login(self, username: str, password: str):
        self.type(self.USERNAME, username)
        self.type(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)
        from pages.accounts_overview_page import AccountsOverviewPage
        return AccountsOverviewPage(self.driver)

    def error_message(self) -> str:
        return self.text_of(self.ERROR)

    def is_displayed(self) -> bool:
        return self.is_visible(self.LOGIN_BTN)

from decimal import Decimal

from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from utils.money import parse_money


class AccountsOverviewPage(BasePage):
    path = "/overview.htm"

    ACCOUNT_ROWS = (By.CSS_SELECTOR, "#accountTable tbody tr")
    ACCOUNT_LINKS = (By.CSS_SELECTOR, "#accountTable tbody td a")

    def is_loaded(self) -> bool:
        return self.is_visible(self.ACCOUNT_LINKS, timeout=10)

    def _rows(self) -> list[list[str]]:
        self.find(self.ACCOUNT_LINKS)  # table is filled by AJAX; wait for at least one account
        return [[td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
                for row in self.driver.find_elements(*self.ACCOUNT_ROWS)]

    def balances(self) -> dict[int, Decimal]:
        """{account_id: balance} for every account row (the 'Total' row is excluded)."""
        return {int(cells[0]): parse_money(cells[1])
                for cells in self._rows() if cells and cells[0].isdigit()}

    def total(self) -> Decimal:
        for cells in self._rows():
            if cells and cells[0] == "Total":
                return parse_money(cells[1])
        raise AssertionError("Total row not found on Accounts Overview")

"""BasePage: explicit-wait wrappers shared by all page objects. Element sync never uses time.sleep()."""
import time
from typing import Tuple

import allure
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from config.config import Config
from utils import rate_limit
from utils.logger import get_logger

Locator = Tuple[str, str]


class BasePage:
    path: str = "/index.htm"

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, Config.EXPLICIT_WAIT)
        self.log = get_logger(self.__class__.__name__)

    @property
    def menu(self):
        from pages.components.side_menu import SideMenu
        return SideMenu(self.driver)

    def open(self):
        url = Config.BASE_URL + self.path
        with allure.step(f"Open {self.__class__.__name__}"):
            self.log.info("Opening %s", url)
            self.driver.get(url)
            self.recover_if_rate_limited()
        return self

    def recover_if_rate_limited(self) -> None:
        """If the CDN served a 429 page instead of the app, back off and reload."""
        for attempt in range(1, rate_limit.MAX_ATTEMPTS):
            if not rate_limit.is_rate_limited_page(self.driver.title, self.driver.page_source):
                return
            delay = rate_limit.backoff_delay(attempt)
            self.log.warning("Browser hit 429 page - reload %d in %.0fs", attempt, delay)
            time.sleep(delay)  # deliberate: backing off a server, not waiting for an element
            self.driver.refresh()

    # ---- element helpers ----
    def find(self, locator: Locator) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def find_all_visible(self, locator: Locator) -> list[WebElement]:
        return self.wait.until(EC.visibility_of_all_elements_located(locator))

    def click(self, locator: Locator) -> None:
        self.log.info("Click %s", locator)
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def type(self, locator: Locator, text: str) -> None:
        el = self.find(locator)
        el.clear()
        el.send_keys(text)

    def text_of(self, locator: Locator) -> str:
        return self.find(locator).text.strip()

    def is_visible(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def select_by_value(self, select_locator: Locator, value: str) -> None:
        """Wait until an AJAX-populated <select> actually contains the option, then pick it."""
        by, sel = select_locator
        if by != By.CSS_SELECTOR:
            raise ValueError("select_by_value expects a CSS locator")
        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f"{sel} option[value='{value}']")))
        Select(self.find(select_locator)).select_by_value(value)

    def wait_for_text(self, locator: Locator, text: str) -> None:
        self.wait.until(EC.text_to_be_present_in_element(locator, text))

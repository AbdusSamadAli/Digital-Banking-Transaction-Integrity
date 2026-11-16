"""Builds local or remote (Selenium Grid) WebDriver instances for Chrome / Firefox / Edge.

Selenium Manager (Selenium 4.6+) resolves local driver binaries automatically,
so no webdriver-manager dependency is needed.
"""
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from config.config import Config


def _options(browser: str, headless: bool):
    width, height = Config.WINDOW_SIZE.split(",")

    if browser == "chrome":
        opts = webdriver.ChromeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"--window-size={width},{height}")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        # Chrome's password-leak popup blocks clicks after login on saucedemo
        opts.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            },
        )
        return opts

    if browser == "firefox":
        opts = webdriver.FirefoxOptions()
        if headless:
            opts.add_argument("-headless")
        opts.add_argument(f"--width={width}")
        opts.add_argument(f"--height={height}")
        return opts

    if browser == "edge":
        opts = webdriver.EdgeOptions()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument(f"--window-size={width},{height}")
        return opts

    raise ValueError(f"Unsupported browser '{browser}'. Use chrome, firefox or edge.")


def create_driver(browser: str, headless: bool, grid_url: str = "") -> WebDriver:
    opts = _options(browser, headless)

    if grid_url:
        return webdriver.Remote(command_executor=grid_url, options=opts)

    local = {"chrome": webdriver.Chrome, "firefox": webdriver.Firefox, "edge": webdriver.Edge}
    return local[browser](options=opts)

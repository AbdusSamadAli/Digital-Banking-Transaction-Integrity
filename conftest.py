"""Fixtures and hooks.

Fixture graph:
    api (session) ──> customer (fresh per test) ──> second_account (API-seeded)
    driver (per test) ─┴─> bank_ui (customer's session injected into the browser)
"""
from pathlib import Path

import allure
import pytest
import requests

from api.bank_api import BankApi
from config.config import Config
from pages.accounts_overview_page import AccountsOverviewPage
from utils.driver_factory import create_driver
from utils.logger import get_logger
from utils.provisioning import ProvisionedCustomer, ProvisioningError, provision_customer

log = get_logger("conftest")
RESULTS_DIR = Path(__file__).parent / "reports" / "allure-results"


def pytest_addoption(parser):
    parser.addoption("--browser", default=Config.BROWSER, choices=["chrome", "firefox", "edge"])
    parser.addoption("--headed", action="store_true", help="Show the browser window")
    parser.addoption("--grid-url", default=Config.GRID_URL, help="Selenium Grid hub, e.g. http://localhost:4444")


# ---------- API ----------
@pytest.fixture(scope="session")
def api() -> BankApi:
    return BankApi()


@pytest.fixture
def customer(api) -> ProvisionedCustomer:
    """A brand-new customer per test -> full data isolation, safe for parallel runs."""
    last_error = None
    for attempt in range(1, 4):  # the public demo server occasionally hiccups during setup
        try:
            return provision_customer(api)
        except (ProvisioningError, requests.RequestException) as exc:
            last_error = exc
            log.warning("Provisioning attempt %d failed: %s", attempt, exc)
    pytest.fail(f"Could not provision a test customer: {last_error}")


@pytest.fixture
def second_account(api, customer):
    """Seed a SAVINGS account through the API so UI tests have somewhere to move money."""
    return api.create_account(customer.id, "SAVINGS", customer.primary_account.id)


# ---------- UI ----------
@pytest.fixture
def driver(request):
    browser = request.config.getoption("--browser")
    headless = Config.HEADLESS and not request.config.getoption("--headed")
    grid_url = request.config.getoption("--grid-url")
    log.info("Starting %s (headless=%s, %s)", browser, headless, grid_url or "local")
    drv = create_driver(browser, headless, grid_url)
    yield drv
    drv.quit()


@pytest.fixture
def bank_ui(driver, customer) -> AccountsOverviewPage:
    """Logged-in browser without going through the login form.

    The HTTP session that registered the customer is already authenticated; copying its
    JSESSIONID into the browser saves a UI login per test. Login itself is tested separately.
    """
    with allure.step("Inject authenticated session cookie into browser"):
        driver.get(Config.BASE_URL + "/index.htm")
        driver.delete_cookie("JSESSIONID")
        driver.add_cookie(customer.session_cookie)
    page = AccountsOverviewPage(driver).open()
    assert page.is_loaded(), "Session injection failed: Accounts Overview did not load"
    return page


# ---------- reporting ----------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """On failure attach screenshot, URL and DOM to Allure."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    drv = item.funcargs.get("driver")
    if drv is None:
        return
    try:
        allure.attach(drv.get_screenshot_as_png(), "screenshot", allure.attachment_type.PNG)
        allure.attach(drv.current_url, "url", allure.attachment_type.TEXT)
        allure.attach(drv.page_source, "page_source", allure.attachment_type.HTML)
    except Exception as exc:  # reporting must never hide the real failure
        log.warning("Could not capture failure artifacts: %s", exc)


def pytest_sessionfinish(session):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    cfg = session.config
    (RESULTS_DIR / "environment.properties").write_text(
        f"Browser={cfg.getoption('--browser')}\n"
        f"Base.URL={Config.BASE_URL}\n"
        f"Execution={'Selenium Grid' if cfg.getoption('--grid-url') else 'Local'}\n",
        encoding="utf-8",
    )

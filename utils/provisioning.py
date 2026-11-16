"""Creates a brand-new bank customer over HTTP (no browser) in ~1 second.

Why: every test gets its own customer, so tests never share balances. That makes them
safe to run in parallel and immune to leftover data from other runs or other people
using the public demo server.

The HTTP session that registered the customer is already logged in, so its JSESSIONID
can be injected into Selenium to skip the UI login for tests that aren't about login.
"""
from dataclasses import dataclass

import allure
import requests

from api.bank_api import BankApi
from api.models import Account, Customer
from config.config import Config
from utils.data_factory import CustomerData
from utils.logger import get_logger
from utils.rate_limit import send_with_backoff

log = get_logger("provisioning")


@dataclass
class ProvisionedCustomer:
    data: CustomerData
    profile: Customer
    primary_account: Account
    web_session: requests.Session

    @property
    def id(self) -> int:
        return self.profile.id

    @property
    def session_cookie(self) -> dict:
        return {"name": "JSESSIONID", "value": self.web_session.cookies.get("JSESSIONID"),
                "path": "/parabank"}


class ProvisioningError(RuntimeError):
    pass


@allure.step("Provision a new customer via HTTP")
def provision_customer(api: BankApi, data: CustomerData | None = None) -> ProvisionedCustomer:
    data = data or CustomerData()
    web = requests.Session()
    url = f"{Config.BASE_URL}/register.htm"
    send_with_backoff(web, "GET", url, timeout=Config.API_TIMEOUT)  # obtain JSESSIONID
    resp = send_with_backoff(web, "POST", url, data=data.as_form(), timeout=Config.API_TIMEOUT)

    if "Your account was created successfully" not in resp.text:
        raise ProvisioningError(f"Registration failed for {data.username} (HTTP {resp.status_code})")

    profile = api.login(data.username, data.password)
    accounts = api.get_accounts(profile.id)
    if len(accounts) != 1:
        raise ProvisioningError(f"Expected 1 default account, got {len(accounts)}")

    log.info("Provisioned customer %s (id=%s, account=%s, balance=%s)",
             data.username, profile.id, accounts[0].id, accounts[0].balance)
    return ProvisionedCustomer(data=data, profile=profile, primary_account=accounts[0], web_session=web)

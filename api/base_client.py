"""Thin wrapper over requests.Session: base URL, timeouts, safe retries, logging and Allure attachments."""
import json

import allure
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.config import Config
from utils.logger import get_logger
from utils.rate_limit import send_with_backoff


class ApiError(AssertionError):
    """Raised when the API returns an unexpected status code."""


class BaseClient:
    def __init__(self, base_url: str, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.log = get_logger(self.__class__.__name__)

        # Retry only idempotent calls on gateway errors. POSTs (transfers!) are never retried
        # automatically: a retried transfer could move money twice and hide a real bug.
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(502, 503, 504),
                      allowed_methods=frozenset({"GET"}))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def request(self, method: str, path: str, expected_status: int | None = 200, **kwargs) -> requests.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", Config.API_TIMEOUT)

        with allure.step(f"API {method} /{path.lstrip('/')}"):
            resp = send_with_backoff(self.session, method, url, **kwargs)
            self.log.info("%s %s -> %s (%.0f ms)", method, resp.url, resp.status_code,
                          resp.elapsed.total_seconds() * 1000)
            allure.attach(self._describe(resp), name=f"{method} {resp.status_code}",
                          attachment_type=allure.attachment_type.TEXT)

        if expected_status is not None and resp.status_code != expected_status:
            raise ApiError(f"{method} {url} returned {resp.status_code}, expected {expected_status}: "
                           f"{resp.text[:300]}")
        return resp

    def get(self, path: str, **kw) -> requests.Response:
        return self.request("GET", path, **kw)

    def post(self, path: str, **kw) -> requests.Response:
        return self.request("POST", path, **kw)

    @staticmethod
    def _describe(resp: requests.Response) -> str:
        req = resp.request
        try:
            body = json.dumps(resp.json(), indent=2)
        except ValueError:
            body = resp.text
        return (f"REQUEST\n{req.method} {req.url}\n{req.body or ''}\n\n"
                f"RESPONSE {resp.status_code} in {resp.elapsed.total_seconds():.3f}s\n{body[:5000]}")

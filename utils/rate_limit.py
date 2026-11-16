"""Rate-limit (HTTP 429) handling shared by the API client, provisioning and the browser.

The public ParaBank server sits behind Cloudflare and rate-limits bursts of traffic.
Parallel test workers can trip it, so every HTTP path in the framework backs off and retries
on 429. It is safe for POSTs too: a 429 means the request was rejected *before* the server
processed it, so retrying cannot transfer money twice (unlike retrying on a 5xx or timeout).
"""
import time

import requests

from utils.logger import get_logger

log = get_logger("rate_limit")

MAX_ATTEMPTS = 6
BASE_DELAY_S = 2.0
MAX_DELAY_S = 30.0


def backoff_delay(attempt: int, retry_after: str | None = None) -> float:
    if retry_after and retry_after.isdigit():
        return min(float(retry_after), MAX_DELAY_S)
    return min(BASE_DELAY_S * 2 ** (attempt - 1), MAX_DELAY_S)  # 2, 4, 8, 16, 30s


def send_with_backoff(session: requests.Session, method: str, url: str, **kwargs) -> requests.Response:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        resp = session.request(method, url, **kwargs)
        if resp.status_code != 429 or attempt == MAX_ATTEMPTS:
            return resp
        delay = backoff_delay(attempt, resp.headers.get("Retry-After"))
        log.warning("429 rate-limited on %s %s - retry %d/%d in %.0fs",
                    method, url, attempt, MAX_ATTEMPTS - 1, delay)
        time.sleep(delay)
    return resp


def is_rate_limited_page(title: str, source: str) -> bool:
    text = f"{title} {source[:3000]}".lower()
    return "429" in title or "too many requests" in text or "you are being rate limited" in text

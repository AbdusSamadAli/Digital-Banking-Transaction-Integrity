# Digital Banking Transaction Integrity Suite

A **hybrid UI + API test automation framework** for [ParaBank](https://parabank.parasoft.com), a demo online-banking app.
It checks that every money movement made in the browser (open account, transfer, bill pay) actually reaches the
backend ledger correctly, so a passing test means more than a green "Transfer Complete!" message.

**Core stack:** Python · **Selenium 4** (UI) · **Requests** (REST API) · **Pytest** (runner and fixtures)
**Supporting:** Pydantic (API contracts) · Allure (reporting) · Docker Selenium Grid · GitHub Actions

---

## The problem it solves

UI-only automation answers "did the page show a success message?". In banking the real question is
*did the money move correctly?* A UI can say "Transfer Complete!" while the debit is missing, the
amount is rounded, or the transaction never reaches the ledger. Also, tests that share one login
and one balance can't run in parallel and break whenever someone else touches the data.

## How it works

| Pattern | Implementation |
|---|---|
| **UI action → API verification** | After each UI transfer, bill payment or new account, the API checks both balances, the total balance across the customer's accounts, and the matching Debit/Credit ledger entries. |
| **API seeding → UI verification** | Accounts and transfers are created through the API, then the Accounts Overview page must show exactly the backend balances and a correct total. |
| **Per-test data isolation** | A `customer` fixture registers a brand-new customer over HTTP (~1 s) for **every test**, so there is no shared state and parallel runs are safe. |
| **Session injection** | The HTTP session that registered the customer is already logged in. Its `JSESSIONID` is injected into Selenium, so there is no UI login per test. |
| **Contract testing** | Every API response is parsed into strict Pydantic models (`extra="forbid"`), so schema drift fails loudly at the parsing step. |
| **Money as `Decimal`** | Balances are never `float`, so cent-level rounding bugs can't hide. |
| **Rate-limit resilience** | The public server sits behind Cloudflare and returns 429s on bursts. One shared backoff helper covers the API client, provisioning and browser page loads. |
| **Safe retries** | GETs retry on 5xx. POSTs (transfers) are retried **only** on 429, because a retried transfer after a timeout could move money twice. |
| **Known-defect tracking** | A defect the suite found (negative transfer amounts accepted) is captured as `xfail(strict=True)`. CI stays green, and the test flips to *failed* the day the bug is fixed, so the marker gets removed. |
| **Layered CI** | API tests run first, and UI/hybrid tests run on a Grid browser matrix only if they pass. Smoke tests run on PRs, full regression on main and nightly, then a merged Allure report is published. |

## Project structure

```
api/
  base_client.py        requests.Session wrapper: timeouts, retries, 429 backoff, Allure req/resp logs
  bank_api.py           ParaBank service object -> returns validated models
  models.py             Pydantic contracts: Customer, Account, Transaction
pages/
  base_page.py          explicit-wait helpers, AJAX-aware <select>, 429 page recovery
  components/side_menu.py   reusable nav component
  login / register / accounts_overview / open_account / transfer / bill_pay pages
tests/
  api/                  contract, business-rule and negative API tests
  ui/                   registration and login
  hybrid/               open account, transfer, bill pay, overview (UI <-> API)
utils/
  provisioning.py       create a customer over HTTP + session for cookie injection
  data_factory.py       Faker-based unique customers and payees
  rate_limit.py         shared 429 backoff
  driver_factory.py     local / Selenium Grid; Chrome, Firefox, Edge
  money.py              "$1,234.50" -> Decimal
conftest.py             fixtures: api, customer, second_account, driver, bank_ui; failure screenshots
docker-compose.yml      Selenium Grid 4 (hub + Chrome + Firefox)
.github/workflows/ci.yml
```

## Test coverage (35 tests)

| Suite | Tests | What is checked |
|---|---|---|
| API | 12 | contract, min-deposit rule, total balance unchanged by transfers (1¢ / decimal / round), double-entry ledger, invalid IDs, bad login, **negative-amount defect** |
| UI | 11 | registration persisted to backend, 4 required-field rules, password mismatch, duplicate username, login/logout, invalid and empty login |
| Hybrid | 12 | open CHECKING/SAVINGS, UI transfer → ledger, overdraft consistency, empty amount, bill pay → debit entry, 3 bill-pay validations, overview == backend |

## Running

```bash
python -m venv .venv
.venv\Scripts\activate                 # Windows  |  source .venv/bin/activate  (mac/linux)
pip install -r requirements.txt

pytest                                 # everything, headless Chrome
pytest -m api                          # API only, no browser (fast)
pytest -m smoke -n 2                   # smoke suite, 2 parallel workers
pytest -m hybrid --headed              # watch the UI <-> API tests run
pytest --browser firefox

docker compose up -d                   # Selenium Grid -> http://localhost:4444
pytest -n 2 --grid-url http://localhost:4444 --browser firefox

allure serve reports/allure-results    # needs Allure CLI (scoop/brew install allure)
```

> Keep parallelism at `-n 2` against the public demo server: it rate-limits bursts. The framework
> recovers from 429s, but backing off costs time.

## Known defect found by this suite

**PB-101: the transfer API accepts negative amounts.** `POST /transfer?amount=-5` returns 200 and moves
money in the reverse direction (out of the *destination* account). Captured in
`tests/api/test_accounts_api.py::test_negative_transfer_rejected` as a strict xfail.

---

## Resume points

**Digital Banking Transaction Integrity Suite** | *Python, Selenium, Requests, Pytest, Pydantic, Allure, Docker, GitHub Actions*

- Built a **hybrid UI + API automation framework** (Selenium + Requests + Pytest, Page Object Model) for an online-banking app. It checks every UI money movement (transfers, bill pay, account opening) against the REST API at balance and ledger level across **35 automated scenarios**, and it found a defect where the transfer API accepted negative amounts.
- Made the suite **parallel-safe and fast** by provisioning an isolated customer per test over HTTP and **injecting the authenticated session into Selenium** to skip UI logins. Added **Pydantic contract validation**, `Decimal`-based money assertions, and **429 rate-limit backoff** so it runs reliably against a shared, rate-limited environment.
- Set up a **layered GitHub Actions pipeline**: API tests gate a **Dockerized Selenium Grid** Chrome/Firefox matrix, with smoke tests on PRs, nightly regression and safe retries, and it publishes **Allure reports** with request/response logs and failure screenshots.

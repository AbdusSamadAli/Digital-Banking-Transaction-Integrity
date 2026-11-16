"""Service object for the ParaBank REST API. Returns validated Pydantic models, never raw dicts."""
from decimal import Decimal

from pydantic import TypeAdapter

from api.base_client import BaseClient
from api.models import Account, Customer, Transaction
from config.config import Config

ACCOUNT_TYPE_CODES = {"CHECKING": 0, "SAVINGS": 1}

_accounts = TypeAdapter(list[Account])
_transactions = TypeAdapter(list[Transaction])


class BankApi(BaseClient):
    def __init__(self, session=None):
        super().__init__(Config.API_URL, session)

    # ---- customers ----
    def login(self, username: str, password: str) -> Customer:
        return Customer.model_validate(self.get(f"login/{username}/{password}").json())

    def get_customer(self, customer_id: int) -> Customer:
        return Customer.model_validate(self.get(f"customers/{customer_id}").json())

    # ---- accounts ----
    def get_accounts(self, customer_id: int) -> list[Account]:
        return _accounts.validate_python(self.get(f"customers/{customer_id}/accounts").json())

    def get_account(self, account_id: int) -> Account:
        return Account.model_validate(self.get(f"accounts/{account_id}").json())

    def balance(self, account_id: int) -> Decimal:
        return self.get_account(account_id).balance

    def total_balance(self, customer_id: int) -> Decimal:
        return sum((a.balance for a in self.get_accounts(customer_id)), Decimal("0"))

    def create_account(self, customer_id: int, account_type: str, from_account_id: int) -> Account:
        resp = self.post("createAccount", params={
            "customerId": customer_id,
            "newAccountType": ACCOUNT_TYPE_CODES[account_type],
            "fromAccountId": from_account_id,
        })
        return Account.model_validate(resp.json())

    # ---- money movement ----
    def transfer(self, from_account_id: int, to_account_id: int, amount: Decimal) -> str:
        resp = self.post("transfer", params={
            "fromAccountId": from_account_id, "toAccountId": to_account_id, "amount": str(amount),
        })
        return resp.text

    # ---- transactions ----
    def get_transactions(self, account_id: int) -> list[Transaction]:
        return _transactions.validate_python(self.get(f"accounts/{account_id}/transactions").json())

    def transaction_ids(self, account_id: int) -> set[int]:
        return {t.id for t in self.get_transactions(account_id)}

    def new_transactions(self, account_id: int, known_ids: set[int]) -> list[Transaction]:
        """Ledger entries posted after a snapshot: assert on exactly what *this* action wrote."""
        return [t for t in self.get_transactions(account_id) if t.id not in known_ids]

    def find_transactions_by_amount(self, account_id: int, amount: Decimal) -> list[Transaction]:
        resp = self.get(f"accounts/{account_id}/transactions/amount/{amount}")
        return _transactions.validate_python(resp.json())

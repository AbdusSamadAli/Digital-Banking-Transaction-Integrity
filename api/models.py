"""Pydantic models = API contract.

Every API response is parsed into one of these. If the backend renames a field, changes a type
or returns an unknown account type, the test fails at the parsing step with a clear
validation error instead of a confusing KeyError deep inside an assertion.

Money is held as Decimal, never float: 0.1 + 0.2 != 0.3 in floating point, and a
balance check that is off by a fraction of a cent is exactly the kind of bug we are testing for.
"""
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Address(_Strict):
    street: str
    city: str
    state: str
    zip_code: str = Field(alias="zipCode")


class Customer(_Strict):
    id: int
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    address: Address
    phone_number: str = Field(alias="phoneNumber")
    ssn: str


class Account(_Strict):
    id: int
    customer_id: int = Field(alias="customerId")
    type: Literal["CHECKING", "SAVINGS", "LOAN"]
    balance: Decimal


class Transaction(_Strict):
    id: int
    account_id: int = Field(alias="accountId")
    type: Literal["Credit", "Debit"]
    date: int
    amount: Decimal = Field(ge=0)
    description: str

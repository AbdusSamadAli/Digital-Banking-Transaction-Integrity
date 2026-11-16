"""Generates realistic, unique test data with Faker so tests never collide on shared data."""
import uuid
from dataclasses import dataclass, field

from faker import Faker

fake = Faker("en_US")


def unique_username(prefix: str = "sdet") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class CustomerData:
    first_name: str = field(default_factory=fake.first_name)
    last_name: str = field(default_factory=fake.last_name)
    street: str = field(default_factory=fake.street_address)
    city: str = field(default_factory=fake.city)
    state: str = field(default_factory=fake.state_abbr)
    zip_code: str = field(default_factory=fake.zipcode)
    phone: str = field(default_factory=lambda: fake.numerify("##########"))
    ssn: str = field(default_factory=fake.ssn)
    username: str = field(default_factory=unique_username)
    password: str = field(default_factory=lambda: fake.password(length=12, special_chars=False))

    def as_form(self, confirm_password: str | None = None) -> dict:
        """Field names exactly as ParaBank's register form posts them."""
        return {
            "customer.firstName": self.first_name,
            "customer.lastName": self.last_name,
            "customer.address.street": self.street,
            "customer.address.city": self.city,
            "customer.address.state": self.state,
            "customer.address.zipCode": self.zip_code,
            "customer.phoneNumber": self.phone,
            "customer.ssn": self.ssn,
            "customer.username": self.username,
            "customer.password": self.password,
            "repeatedPassword": self.password if confirm_password is None else confirm_password,
        }


@dataclass
class PayeeData:
    name: str = field(default_factory=fake.company)
    street: str = field(default_factory=fake.street_address)
    city: str = field(default_factory=fake.city)
    state: str = field(default_factory=fake.state_abbr)
    zip_code: str = field(default_factory=fake.zipcode)
    phone: str = field(default_factory=lambda: fake.numerify("##########"))
    account_number: str = field(default_factory=lambda: fake.numerify("#####"))

from decimal import Decimal


def parse_money(text: str) -> Decimal:
    """'$1,234.50' -> Decimal('1234.50'); '-$100.00' -> Decimal('-100.00')."""
    cleaned = text.strip().replace("$", "").replace(",", "")
    return Decimal(cleaned)

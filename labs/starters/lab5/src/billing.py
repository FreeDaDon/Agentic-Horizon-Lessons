from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    customer_id: str
    cents: int


def total_cents(invoices: list[Invoice]) -> int:
    return sum(invoice.cents for invoice in invoices)


def apply_discount(cents: int, percent: int) -> int:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return cents * (100 - percent) // 100

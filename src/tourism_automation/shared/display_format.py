"""Helpers for formatting numeric values as display strings."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def percent_text(value: Any) -> str | None:
    if value is None:
        return None
    decimal_value = Decimal(str(value)) * Decimal("100")
    return f"{decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}%"


def currency_text(value: Any) -> str | None:
    if value is None:
        return None
    decimal_value = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"￥{decimal_value:,.2f}"

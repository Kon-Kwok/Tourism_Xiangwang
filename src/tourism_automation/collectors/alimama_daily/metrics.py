"""Metric helpers for Alimama daily advertising reports."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def decimal_or_zero(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


def int_or_zero(value: Any) -> int:
    return int(decimal_or_zero(value))


def money(value: Any) -> Decimal:
    return decimal_or_zero(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def ratio(numerator: Any, denominator: Any, places: str) -> Decimal:
    denominator_value = decimal_or_zero(denominator)
    if denominator_value == 0:
        return Decimal("0").quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return (decimal_or_zero(numerator) / denominator_value).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def base_metrics(row: dict[str, Any], *, date_time: str) -> dict[str, Any]:
    metrics = {
        "date_time": date_time,
        "cost": money(row.get("cost")),
        "imp": int_or_zero(row.get("imp")),
        "click": int_or_zero(row.get("click")),
        "order_count": int_or_zero(row.get("order_count")),
        "sales": money(row.get("sales")),
        "shopping_cart": int_or_zero(row.get("shopping_cart")),
        "bookmark_product": int_or_zero(row.get("bookmark_product")),
        "bookmark_store": int_or_zero(row.get("bookmark_store")),
    }
    metrics.update(calculate_metrics(metrics))
    return metrics


def calculate_metrics(metrics: dict[str, Any]) -> dict[str, Decimal]:
    return {
        "ctr": ratio(metrics["click"], metrics["imp"], "0.000001"),
        "cpc": ratio(metrics["cost"], metrics["click"], "0.01"),
        "cpm": ratio(decimal_or_zero(metrics["cost"]) * Decimal("1000"), metrics["imp"], "0.01"),
        "roi": ratio(metrics["sales"], metrics["cost"], "0.0001"),
        "cvr": ratio(metrics["order_count"], metrics["click"], "0.000001"),
        "asp": ratio(metrics["sales"], metrics["order_count"], "0.01"),
        "cporder": ratio(metrics["cost"], metrics["order_count"], "0.01"),
        "cpshopping_cart": ratio(metrics["cost"], metrics["shopping_cart"], "0.01"),
        "collection_cart_cost": ratio(
            metrics["cost"],
            decimal_or_zero(metrics["shopping_cart"]) + decimal_or_zero(metrics["bookmark_product"]),
            "0.01",
        ),
        "collection_cart_count": decimal_or_zero(metrics["shopping_cart"]) + decimal_or_zero(metrics["bookmark_product"]),
        "collection_cart_rate": ratio(
            decimal_or_zero(metrics["shopping_cart"]) + decimal_or_zero(metrics["bookmark_product"]),
            metrics["click"],
            "0.000001",
        ),
    }

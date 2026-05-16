"""Excel-compatible calculation rules for Alimama daily reports."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from tourism_automation.collectors.alimama_daily.metrics import decimal_or_zero, int_or_zero, money, ratio


BASE_FIELDS = [
    "cost",
    "imp",
    "click",
    "order_count",
    "sales",
    "shopping_cart",
    "bookmark_product",
    "bookmark_store",
]

SHEET_FIELDS = {
    "star_store": BASE_FIELDS
    + ["ctr", "cpc", "cpm", "roi", "cvr", "asp", "cporder", "cpshopping_cart", "cart_rate"],
    "tmall_express": BASE_FIELDS
    + [
        "ctr",
        "cpc",
        "roi",
        "cvr",
        "asp",
        "cporder",
        "cpshopping_cart",
        "collection_cart_cost",
        "collection_cart_count",
        "collection_cart_rate",
    ],
    "gravity_rubiks_cube": BASE_FIELDS
    + ["ctr", "cpc", "cpm", "roi", "cvr", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"],
    "wanxiangtai": BASE_FIELDS
    + ["ctr", "cpc", "cpm", "roi", "cvr", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"],
    "wanxiangtai_2": ["data_source"]
    + BASE_FIELDS
    + ["ctr", "cpc", "cpm", "roi", "cvr", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"],
}


def calculate_excel_metrics(
    row: dict[str, Any],
    *,
    date_time: str,
    sheet: str,
    previous_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = normalize_base_metrics(row, date_time=date_time)
    metrics.update(_same_row_metrics(metrics))
    return _select_fields(metrics, sheet)


def calculate_wanxiangtai_2_total(rows: list[dict[str, Any]], *, date_time: str) -> dict[str, Any]:
    raw = {
        "cost": sum(decimal_or_zero(row.get("cost")) for row in rows),
        "imp": sum(int_or_zero(row.get("imp")) for row in rows),
        "click": sum(int_or_zero(row.get("click")) for row in rows),
        "order_count": sum(int_or_zero(row.get("order_count")) for row in rows),
        "sales": sum(decimal_or_zero(row.get("sales")) for row in rows),
        "shopping_cart": sum(int_or_zero(row.get("shopping_cart")) for row in rows),
        "bookmark_product": sum(int_or_zero(row.get("bookmark_product")) for row in rows),
        "bookmark_store": sum(int_or_zero(row.get("bookmark_store")) for row in rows),
    }
    raw["data_source"] = "小计"
    total = calculate_excel_metrics(raw, date_time=date_time, sheet="wanxiangtai_2")
    total["data_source"] = "小计"
    return total


def normalize_base_metrics(row: dict[str, Any], *, date_time: str) -> dict[str, Any]:
    return {
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


def _same_row_metrics(metrics: dict[str, Any]) -> dict[str, Decimal]:
    collection_cart_count = decimal_or_zero(metrics["shopping_cart"]) + decimal_or_zero(metrics["bookmark_product"])
    return {
        "ctr": ratio(metrics["click"], metrics["imp"], "0.000001"),
        "cpc": ratio(metrics["cost"], metrics["click"], "0.01"),
        "cpm": ratio(decimal_or_zero(metrics["cost"]) * Decimal("1000"), metrics["imp"], "0.01"),
        "roi": ratio(metrics["sales"], metrics["cost"], "0.0001"),
        "cvr": ratio(metrics["order_count"], metrics["click"], "0.000001"),
        "asp": ratio(metrics["sales"], metrics["order_count"], "0.01"),
        "cporder": ratio(metrics["cost"], metrics["order_count"], "0.01"),
        "cpshopping_cart": ratio(metrics["cost"], metrics["shopping_cart"], "0.01"),
        "cart_rate": ratio(metrics["shopping_cart"], metrics["click"], "0.000001"),
        "collection_cart_cost": ratio(metrics["cost"], collection_cart_count, "0.01"),
        "collection_cart_count": collection_cart_count,
        "collection_cart_rate": ratio(collection_cart_count, metrics["click"], "0.000001"),
    }


def _select_fields(metrics: dict[str, Any], sheet: str) -> dict[str, Any]:
    selected = {"date_time": metrics["date_time"]}
    for field in SHEET_FIELDS[sheet]:
        if field in metrics:
            selected[field] = metrics[field]
    return selected

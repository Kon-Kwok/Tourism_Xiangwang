"""Normalize Alimama star store report payloads."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


CENT = Decimal("100")


def normalize_star_store_payload(payload: dict[str, Any], *, biz_date: str) -> dict[str, Any]:
    row = _extract_sum_row(payload)
    if not row or not _has_metric_values(row):
        return {
            "status": "no_data",
            "date_time": biz_date,
            "metrics": None,
            "raw": payload,
        }

    metrics = {
        "date_time": biz_date,
        "cost": _money_from_cents(row.get("cost")),
        "imp": _int_or_none(row.get("impression")),
        "click": _int_or_none(row.get("click")),
        "order_count": _int_or_none(row.get("transactionshippingtotal")),
        "sales": _money_from_cents(row.get("transactiontotal")),
        "shopping_cart": _int_or_none(row.get("carttotal")),
        "bookmark_product": _int_or_none(row.get("favitemtotal")),
        "bookmark_store": _int_or_none(row.get("favshoptotal")),
    }
    metrics.update(_calculated_metrics(metrics))
    return {
        "status": "success",
        "date_time": biz_date,
        "metrics": metrics,
        "raw": payload,
    }


def _extract_sum_row(payload: dict[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data", {})
    rows = data.get("result")
    if rows:
        return rows[0]
    response = data.get("rptQueryResp", {})
    rows = response.get("rptDataSum") or response.get("rptDataDaily") or []
    if not rows:
        return None
    return rows[0]


def _has_metric_values(row: dict[str, Any]) -> bool:
    metric_keys = (
        "impression",
        "cost",
        "click",
        "transactionshippingtotal",
        "transactiontotal",
        "carttotal",
        "favitemtotal",
        "favshoptotal",
    )
    return any(row.get(key) is not None for key in metric_keys)


def _money_from_cents(value: Any) -> Decimal | None:
    decimal_value = _decimal_or_none(value)
    if decimal_value is None:
        return None
    return (decimal_value / CENT).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    return int(Decimal(str(value)))


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _ratio(numerator: Any, denominator: Any, places: str) -> Decimal | None:
    numerator_value = _decimal_or_none(numerator)
    denominator_value = _decimal_or_none(denominator)
    if numerator_value is None or denominator_value in (None, Decimal("0")):
        return None
    return (numerator_value / denominator_value).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _calculated_metrics(metrics: dict[str, Any]) -> dict[str, Decimal | None]:
    return {
        "ctr": _ratio(metrics["click"], metrics["imp"], "0.000001"),
        "cpc": _ratio(metrics["cost"], metrics["click"], "0.01"),
        "cpm": _ratio(_decimal_or_none(metrics["cost"]) * Decimal("1000") if metrics["cost"] is not None else None, metrics["imp"], "0.01"),
        "roi": _ratio(metrics["sales"], metrics["cost"], "0.0001"),
        "cvr": _ratio(metrics["order_count"], metrics["click"], "0.000001"),
        "asp": _ratio(metrics["sales"], metrics["order_count"], "0.01"),
        "cporder": _ratio(metrics["cost"], metrics["order_count"], "0.01"),
        "cpshopping_cart": _ratio(metrics["cost"], metrics["shopping_cart"], "0.01"),
        "cart_rate": _ratio(metrics["shopping_cart"], metrics["click"], "0.000001"),
    }

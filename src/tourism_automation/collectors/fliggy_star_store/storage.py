"""Persistence helpers for the Fliggy star store report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tourism_automation.shared.display_format import currency_text, percent_text


PERCENT_FIELDS = {"ctr", "cvr", "cart_rate"}
MONEY_FIELDS = {"cost", "sales", "cpc", "cpm", "asp", "cporder", "cpshopping_cart"}


@dataclass
class FliggyStarStoreStorage:
    config: dict[str, Any]

    def _connect(self):
        try:
            import pymysql
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pymysql is required for MySQL writes") from exc
        return pymysql.connect(**self.config)

    def save(self, result: dict[str, Any]) -> int | None:
        if result.get("status") != "success" or not result.get("metrics"):
            return None

        metrics = result["metrics"]
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM star_store WHERE date_time=%s",
                    (metrics["date_time"],),
                )
                cursor.execute(
                    """
                    INSERT INTO star_store
                    (date_time, cost, imp, click, order_count, sales,
                     shopping_cart, bookmark_product, bookmark_store,
                     ctr, cpc, cpm, roi, cvr, asp, cporder, cpshopping_cart, cart_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (metrics["date_time"],) + _metric_values(metrics),
                )
                cursor.execute(
                    "SELECT id FROM star_store WHERE date_time=%s ORDER BY id LIMIT 1",
                    (metrics["date_time"],),
                )
                row = cursor.fetchone()
            conn.commit()
        return int(row[0]) if row else None


def _metric_values(metrics: dict[str, Any]) -> tuple[Any, ...]:
    return (
        _storage_value("cost", metrics["cost"]),
        metrics["imp"],
        metrics["click"],
        metrics["order_count"],
        _storage_value("sales", metrics["sales"]),
        metrics["shopping_cart"],
        metrics["bookmark_product"],
        metrics["bookmark_store"],
        _storage_value("ctr", metrics["ctr"]),
        _storage_value("cpc", metrics["cpc"]),
        _storage_value("cpm", metrics["cpm"]),
        metrics["roi"],
        _storage_value("cvr", metrics["cvr"]),
        _storage_value("asp", metrics["asp"]),
        _storage_value("cporder", metrics["cporder"]),
        _storage_value("cpshopping_cart", metrics["cpshopping_cart"]),
        _storage_value("cart_rate", metrics["cart_rate"]),
    )


def _storage_value(field: str, value: Any) -> Any:
    if field not in PERCENT_FIELDS or value is None:
        if field in MONEY_FIELDS:
            return currency_text(value)
        return value
    return percent_text(value)

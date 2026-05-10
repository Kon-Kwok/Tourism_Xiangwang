"""Persistence helpers for the Fliggy star store report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
        metrics["cost"],
        metrics["imp"],
        metrics["click"],
        metrics["order_count"],
        metrics["sales"],
        metrics["shopping_cart"],
        metrics["bookmark_product"],
        metrics["bookmark_store"],
        metrics["ctr"],
        metrics["cpc"],
        metrics["cpm"],
        metrics["roi"],
        metrics["cvr"],
        metrics["asp"],
        metrics["cporder"],
        metrics["cpshopping_cart"],
        metrics["cart_rate"],
    )

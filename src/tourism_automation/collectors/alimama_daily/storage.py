"""Persistence for Alimama daily advertising reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


TABLE_CHANNELS = {
    "star_store": "star_store",
    "tmall_express": "tmall_express",
    "gravity_rubiks_cube": "gravity_rubiks_cube",
    "wanxiangtai": "wanxiangtai",
}

TABLE_FIELDS = {
    "star_store": [
        "cost",
        "imp",
        "click",
        "order_count",
        "sales",
        "shopping_cart",
        "bookmark_product",
        "bookmark_store",
        "ctr",
        "cpc",
        "cpm",
        "roi",
        "cvr",
        "asp",
        "cporder",
        "cpshopping_cart",
        "cart_rate",
    ],
    "tmall_express": [
        "cost",
        "imp",
        "click",
        "order_count",
        "sales",
        "shopping_cart",
        "bookmark_product",
        "bookmark_store",
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
    "gravity_rubiks_cube": [
        "cost",
        "imp",
        "click",
        "order_count",
        "sales",
        "shopping_cart",
        "bookmark_product",
        "bookmark_store",
        "ctr",
        "cpc",
        "cpm",
        "roi",
        "cvr",
        "collection_cart_cost",
        "collection_cart_count",
        "collection_cart_rate",
    ],
    "wanxiangtai": [
        "cost",
        "imp",
        "click",
        "order_count",
        "sales",
        "shopping_cart",
        "bookmark_product",
        "bookmark_store",
        "ctr",
        "cpc",
        "cpm",
        "roi",
        "cvr",
        "collection_cart_cost",
        "collection_cart_count",
        "collection_cart_rate",
    ],
}

WANXIANGTAI_2_FIELDS = [
    "data_source",
    "cost",
    "imp",
    "click",
    "order_count",
    "sales",
    "shopping_cart",
    "bookmark_product",
    "bookmark_store",
    "ctr",
    "cpc",
    "cpm",
    "roi",
    "cvr",
    "collection_cart_cost",
    "collection_cart_count",
    "collection_cart_rate",
]


@dataclass
class AlimamaDailyStorage:
    config: dict[str, Any]

    def _connect(self):
        try:
            import pymysql
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pymysql is required for MySQL writes") from exc
        return pymysql.connect(**self.config)

    def save(self, result: dict[str, Any]) -> dict[str, bool]:
        channels = result["channels"]
        saved: dict[str, bool] = {}
        with self._connect() as conn:
            with conn.cursor() as cursor:
                for table in TABLE_CHANNELS:
                    cursor.execute(f"DELETE FROM {table} WHERE date_time=%s", (result["date_time"],))
                cursor.execute("DELETE FROM wanxiangtai_2 WHERE date_time=%s", (result["date_time"],))

                for table, channel in TABLE_CHANNELS.items():
                    fields = TABLE_FIELDS[table]
                    metrics = channels[channel]
                    values = tuple(metrics[field] for field in fields)
                    columns = "date_time, " + ", ".join(fields)
                    placeholders = ", ".join(["%s"] * (len(fields) + 1))
                    cursor.execute(
                        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                        (result["date_time"],) + values,
                    )
                    saved[table] = True
                self._save_wanxiangtai_2_rows(cursor, result)
                saved["wanxiangtai_2"] = True
            conn.commit()
        return saved

    def _save_wanxiangtai_2_rows(self, cursor, result: dict[str, Any]) -> None:
        for data_source, metrics in result["wanxiangtai_2_rows"].items():
            row = {**metrics, "data_source": metrics.get("data_source", data_source)}
            values = tuple(row[field] for field in WANXIANGTAI_2_FIELDS)
            columns = "date_time, " + ", ".join(WANXIANGTAI_2_FIELDS)
            placeholders = ", ".join(["%s"] * (len(WANXIANGTAI_2_FIELDS) + 1))
            cursor.execute(
                f"INSERT INTO wanxiangtai_2 ({columns}) VALUES ({placeholders})",
                (result["date_time"],) + values,
            )

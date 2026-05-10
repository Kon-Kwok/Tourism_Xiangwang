"""MySQL schema and persistence helpers for SYCM."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional

try:
    import pymysql
except ImportError:  # pragma: no cover
    pymysql = None


SCHEMA_SQL = [
    """
    CREATE TABLE IF NOT EXISTS collection_batches (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        page_code VARCHAR(64) NOT NULL,
        biz_date DATE NOT NULL,
        shop_name VARCHAR(255) NOT NULL,
        status VARCHAR(32) NOT NULL,
        started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        finished_at TIMESTAMP NULL DEFAULT NULL,
        error_message TEXT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生意参谋采集批次';
    """,
    """
    CREATE TABLE IF NOT EXISTS api_raw_payloads (
        batch_id BIGINT NOT NULL,
        endpoint_code VARCHAR(64) NOT NULL,
        payload_json LONGTEXT NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (batch_id, endpoint_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生意参谋原始接口响应';
    """,
    """
    CREATE TABLE IF NOT EXISTS homepage_metrics (
        biz_date DATE NOT NULL,
        page_code VARCHAR(64) NOT NULL,
        shop_name VARCHAR(255) NOT NULL,
        metric_code VARCHAR(128) NOT NULL,
        metric_value DECIMAL(20,6) NULL,
        cycle_crc DECIMAL(20,10) NULL,
        sync_crc DECIMAL(20,10) NULL,
        year_sync_crc DECIMAL(20,10) NULL,
        collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        batch_id BIGINT NOT NULL,
        PRIMARY KEY (biz_date, page_code, metric_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生意参谋首页核心指标';
    """,
    """
    CREATE TABLE IF NOT EXISTS homepage_trends (
        biz_date DATE NOT NULL,
        stat_date DATE NOT NULL,
        page_code VARCHAR(64) NOT NULL,
        shop_name VARCHAR(255) NOT NULL,
        metric_code VARCHAR(128) NOT NULL,
        self_value DECIMAL(20,6) NULL,
        rival_avg_value DECIMAL(20,6) NULL,
        rival_good_value DECIMAL(20,6) NULL,
        collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        batch_id BIGINT NOT NULL,
        PRIMARY KEY (biz_date, stat_date, page_code, metric_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生意参谋首页趋势序列';
    """,
]


@dataclass
class MySQLSink:
    config: Dict[str, object]

    def _connect(self):
        if pymysql is None:
            raise RuntimeError("pymysql is required for MySQL writes")
        return pymysql.connect(**self.config)

    def ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                for sql in SCHEMA_SQL:
                    cursor.execute(sql)
            conn.commit()

    def write_home_collection(self, payload: Dict[str, object]) -> int:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                self._delete_existing_day(cursor, payload["metrics"])
                batch_id = self._insert_batch(cursor, payload)
                self._insert_metrics(cursor, batch_id, payload["metrics"])
                self._insert_trends(cursor, batch_id, payload["trends"])
                self._insert_raw_payloads(cursor, batch_id, payload["raw_payloads"])
            conn.commit()
        return batch_id

    def _delete_existing_day(self, cursor, metrics: List[Dict[str, object]]) -> None:
        first = metrics[0]
        params = (first["biz_date"], first["page_code"], first["shop_name"])
        cursor.execute(
            "DELETE FROM homepage_metrics WHERE biz_date=%s AND page_code=%s AND shop_name=%s",
            params,
        )
        cursor.execute(
            "DELETE FROM homepage_trends WHERE biz_date=%s AND page_code=%s AND shop_name=%s",
            params,
        )
        cursor.execute(
            """
            DELETE r
            FROM api_raw_payloads r
            JOIN collection_batches b ON b.id = r.batch_id
            WHERE b.biz_date=%s AND b.page_code=%s AND b.shop_name=%s
            """,
            params,
        )
        cursor.execute(
            "DELETE FROM collection_batches WHERE biz_date=%s AND page_code=%s AND shop_name=%s",
            params,
        )

    def _insert_batch(self, cursor, payload: Dict[str, object]) -> int:
        metrics = payload["metrics"]
        cursor.execute(
            """
            INSERT INTO collection_batches (page_code, biz_date, shop_name, status, finished_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                metrics[0]["page_code"],
                metrics[0]["biz_date"],
                metrics[0]["shop_name"],
                "success",
                datetime.utcnow(),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_metrics(self, cursor, batch_id: int, metrics: Iterable[Dict[str, object]]) -> None:
        cursor.executemany(
            """
            INSERT INTO homepage_metrics
            (biz_date, page_code, shop_name, metric_code, metric_value, cycle_crc, sync_crc, year_sync_crc, batch_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    item["biz_date"],
                    item["page_code"],
                    item["shop_name"],
                    item["metric_code"],
                    item["metric_value"],
                    item["cycle_crc"],
                    item["sync_crc"],
                    item["year_sync_crc"],
                    batch_id,
                )
                for item in metrics
            ],
        )

    def _insert_trends(self, cursor, batch_id: int, trends: Iterable[Dict[str, object]]) -> None:
        cursor.executemany(
            """
            INSERT INTO homepage_trends
            (biz_date, stat_date, page_code, shop_name, metric_code, self_value, rival_avg_value, rival_good_value, batch_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    item["biz_date"],
                    item["stat_date"],
                    item["page_code"],
                    item["shop_name"],
                    item["metric_code"],
                    item["self_value"],
                    item["rival_avg_value"],
                    item["rival_good_value"],
                    batch_id,
                )
                for item in trends
            ],
        )

    def _insert_raw_payloads(self, cursor, batch_id: int, payloads: Dict[str, object]) -> None:
        cursor.executemany(
            """
            INSERT INTO api_raw_payloads (batch_id, endpoint_code, payload_json)
            VALUES (%s, %s, %s)
            """,
            [
                (batch_id, endpoint_code, json.dumps(payload, ensure_ascii=False))
                for endpoint_code, payload in payloads.items()
            ],
        )

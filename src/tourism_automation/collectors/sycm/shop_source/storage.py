"""SYCM店铺来源数据库存储"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

try:
    import pymysql
except ImportError:  # pragma: no cover
    pymysql = None


@dataclass
class ShopSourceStorage:
    """店铺来源数据库存储"""
    config: Dict[str, object]

    def _connect(self):
        if pymysql is None:
            raise RuntimeError("pymysql is required for MySQL writes")
        return pymysql.connect(**self.config)

    def ensure_schema(self) -> None:
        """确保数据库表结构存在"""
        conn = self._connect()
        try:
            cursor = conn.cursor()
            for sql in self._get_schema_sql():
                cursor.execute(sql)
            conn.commit()
        finally:
            conn.close()

    def _get_schema_sql(self) -> Iterable[str]:
        """获取建表SQL"""
        yield """
            CREATE TABLE IF NOT EXISTS shop_source_collection_batches (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                biz_date DATE NOT NULL,
                shop_name VARCHAR(255) NOT NULL,
                status VARCHAR(32) NOT NULL,
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP NULL,
                error_message TEXT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SYCM店铺来源采集批次'
        """

        yield """
            CREATE TABLE IF NOT EXISTS shop_source_metrics (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                batch_id BIGINT NOT NULL,
                biz_date DATE NOT NULL,
                page_code VARCHAR(64) NOT NULL,
                shop_name VARCHAR(255) NOT NULL,
                source_name VARCHAR(255) NOT NULL,
                uv BIGINT NOT NULL,
                uv_ratio DECIMAL(10,6) NULL,
                page_id INT NULL,
                channel_type VARCHAR(32) NULL,
                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_batch_date (batch_id, biz_date),
                INDEX idx_date_source (biz_date, source_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SYCM店铺来源指标'
        """

    def save(self, data: Dict[str, object]) -> int:
        """保存采集数据到数据库

        Args:
            data: 采集器返回的数据

        Returns:
            int: 批次ID
        """
        conn = self._connect()
        try:
            cursor = conn.cursor()

            # 创建批次记录
            summary = data.get('summary', {})
            cursor.execute("""
                DELETE m
                FROM shop_source_metrics m
                JOIN shop_source_collection_batches b ON b.id = m.batch_id
                WHERE b.biz_date = %s AND b.shop_name = %s
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
            ))
            cursor.execute("""
                DELETE FROM shop_source_collection_batches
                WHERE biz_date = %s AND shop_name = %s
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
            ))

            cursor.execute("""
                INSERT INTO shop_source_collection_batches
                (biz_date, shop_name, status, started_at)
                VALUES (%s, %s, %s, NOW())
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
                'success'
            ))

            batch_id = cursor.lastrowid
            metrics = data.get('metrics', [])

            # 插入指标数据
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO shop_source_metrics
                    (batch_id, biz_date, page_code, shop_name, source_name, uv, uv_ratio, page_id, channel_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    batch_id,
                    metric.get('biz_date'),
                    metric.get('page_code'),
                    metric.get('shop_name'),
                    metric.get('source_name'),
                    metric.get('uv'),
                    metric.get('uv_ratio'),
                    metric.get('page_id'),
                    metric.get('channel_type')
                ))

            conn.commit()
            return batch_id

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

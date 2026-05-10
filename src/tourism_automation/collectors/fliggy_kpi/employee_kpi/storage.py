"""飞猪客服KPI数据库存储"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass
class EmployeeKpiStorage:
    """员工KPI数据库存储"""
    config: Dict[str, object]

    def _connect(self):
        """创建数据库连接"""
        try:
            import pymysql
        except ImportError:
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
            CREATE TABLE IF NOT EXISTS employee_kpi_collection_batches (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                biz_date DATE NOT NULL,
                shop_name VARCHAR(255) NOT NULL,
                kpi_id VARCHAR(64) NOT NULL,
                status VARCHAR(32) NOT NULL,
                started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP NULL,
                error_message TEXT NULL,
                INDEX idx_date_shop (biz_date, shop_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='飞猪客服KPI采集批次'
        """

        yield """
            CREATE TABLE IF NOT EXISTS employee_kpi_metrics (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                batch_id BIGINT NOT NULL,
                biz_date DATE NOT NULL,
                employee_name VARCHAR(255) NOT NULL,
                service_count INT NOT NULL COMMENT '接待人数',
                avg_response_seconds DECIMAL(10,2) NULL COMMENT '平均响应时间(秒)',
                reply_rate DECIMAL(10,6) NULL COMMENT '回复率',
                conversion_rate DECIMAL(10,6) NULL COMMENT '询单->最终付款转化率',
                work_days INT NULL COMMENT '上班天数',
                satisfaction_participation_rate DECIMAL(10,6) NULL COMMENT '服务满意度评价参与率',
                customer_satisfaction_rate DECIMAL(10,6) NULL COMMENT '客户满意率',
                very_satisfied_count INT NULL COMMENT '很满意数',
                satisfied_count INT NULL COMMENT '满意数',
                neutral_count INT NULL COMMENT '一般数',
                dissatisfied_count INT NULL COMMENT '不满意数',
                very_dissatisfied_count INT NULL COMMENT '很不满意数',
                shop_name VARCHAR(255) NOT NULL,
                collected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_batch_date (batch_id, biz_date),
                INDEX idx_employee_date (employee_name, biz_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='飞猪客服KPI指标'
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
                FROM employee_kpi_metrics m
                JOIN employee_kpi_collection_batches b ON b.id = m.batch_id
                WHERE b.biz_date = %s
                  AND b.shop_name = %s
                  AND b.kpi_id = %s
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
                summary.get('kpi_id'),
            ))
            cursor.execute("""
                DELETE FROM employee_kpi_collection_batches
                WHERE biz_date = %s AND shop_name = %s AND kpi_id = %s
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
                summary.get('kpi_id'),
            ))

            cursor.execute("""
                INSERT INTO employee_kpi_collection_batches
                (biz_date, shop_name, kpi_id, status, started_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (
                summary.get('collection_date'),
                summary.get('shop_name'),
                summary.get('kpi_id'),
                'success'
            ))

            batch_id = cursor.lastrowid
            metrics = data.get('metrics', [])

            # 插入指标数据
            for metric in metrics:
                cursor.execute("""
                    INSERT INTO employee_kpi_metrics
                    (batch_id, biz_date, employee_name, service_count, avg_response_seconds,
                     reply_rate, conversion_rate, work_days, satisfaction_participation_rate,
                     customer_satisfaction_rate, very_satisfied_count, satisfied_count,
                     neutral_count, dissatisfied_count, very_dissatisfied_count, shop_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    batch_id,
                    metric.get('biz_date'),
                    metric.get('employee_name'),
                    metric.get('service_count'),
                    metric.get('avg_response_seconds'),
                    metric.get('reply_rate'),
                    metric.get('conversion_rate'),
                    metric.get('work_days'),
                    metric.get('satisfaction_participation_rate'),
                    metric.get('customer_satisfaction_rate'),
                    metric.get('very_satisfied_count'),
                    metric.get('satisfied_count'),
                    metric.get('neutral_count'),
                    metric.get('dissatisfied_count'),
                    metric.get('very_dissatisfied_count'),
                    metric.get('shop_name')
                ))

            conn.commit()
            return batch_id

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

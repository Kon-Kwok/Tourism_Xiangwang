#!/usr/bin/env python3
"""飞猪订单数据入库脚本"""

import json
import sys
from decimal import Decimal

def _quote_string(value):
    if value in (None, ""):
        return "NULL"
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"

def _to_decimal(value):
    if value in (None, ""):
        return None
    # 移除货币符号
    if isinstance(value, str):
        value = value.replace("￥", "").replace(",", "").strip()
    return Decimal(str(value))

def _format_decimal(value):
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return "NULL"
    return str(decimal_value.quantize(Decimal("0.00")))

def _format_int(value):
    if value in (None, ""):
        return "NULL"
    return str(int(value))

def build_upsert_sql(payload):
    summary = payload.get("summary", {})
    rows = payload.get("rows", [])

    values = []
    for row in rows:
        # 提取金额（去除￥符号）
        actual_fee = _format_decimal(row.get("actual_fee"))

        values.append(
            "("
            + ", ".join([
                _quote_string(row.get("orderId")),
                _quote_string(row.get("item_title")),
                _quote_string(row.get("package_type")),
                _format_int(row.get("buy_mount")),
                actual_fee,
                _quote_string(row.get("order_time")),
                _quote_string(row.get("status_text")),
                _quote_string(summary.get("deal_start", "").split()[0]),  # 提取日期
            ])
            + ")"
        )

    if not values:
        return "-- 没有数据需要入库\n"

    return f"""
-- 飞猪订单数据
-- 日期: {summary.get('deal_start', '').split()[0]}
-- 订单数: {summary.get('order_count')}
-- GMV: {summary.get('gmv')}

-- 创建表（如果不存在）
CREATE TABLE IF NOT EXISTS order_list (
    order_id VARCHAR(50) PRIMARY KEY,
    item_title VARCHAR(300),
    package_type VARCHAR(200),
    buy_mount INT,
    actual_fee DECIMAL(10,2),
    order_time DATETIME,
    status_text VARCHAR(50),
    order_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 清理当天旧数据，避免重复入库
DELETE FROM order_list WHERE order_date = '{summary.get('deal_start', '').split()[0]}';

-- 插入数据
INSERT INTO order_list
(order_id, item_title, package_type, buy_mount, actual_fee, order_time, status_text, order_date)
VALUES
{',\n'.join(values)};
"""

def main():
    payload = json.load(sys.stdin)
    sql = build_upsert_sql(payload)
    sys.stdout.write(sql)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

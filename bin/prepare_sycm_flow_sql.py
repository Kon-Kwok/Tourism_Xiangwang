#!/usr/bin/env python3
"""SYCM流量数据入库脚本"""

import json
import sys

def _format_int(value):
    if value in (None, ""):
        return "0"
    return str(int(value))

def _format_follow_count(value):
    if value in (None, ""):
        return "0"
    return str(int(value))

def build_upsert_sql(payload):
    summary = payload.get("summary", {})
    rows = payload.get("rows", [])

    if not rows:
        return "-- 没有数据需要入库\n"

    row = rows[0]
    biz_date = summary.get("biz_date", "")
    follow_count = _format_follow_count(row.get('关注店铺人数'))

    return f"""
-- SYCM流量监控数据
-- 日期: {biz_date}

INSERT INTO Xiangwang.shop_daily_key_data (日期, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_daily_key_data
    WHERE 日期 = '{biz_date}'
);

UPDATE Xiangwang.shop_daily_key_data
SET total_uv = {_format_int(row.get('访客数'))},
    total_pv = {_format_int(row.get('浏览量'))},
    流量来源广告_uv = {_format_int(row.get('广告流量'))},
    流量来源平台_uv = {_format_int(row.get('平台流量'))}
WHERE 日期 = '{biz_date}';

-- 写入店铺数据每日登记的关注店铺人数
INSERT INTO Xiangwang.shop_data_daily_registration (`日期`, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_data_daily_registration
    WHERE `日期` = '{biz_date}'
);

UPDATE Xiangwang.shop_data_daily_registration
SET `关注店铺人数` = {follow_count}
WHERE `日期` = '{biz_date}';
"""

def main():
    payload = json.load(sys.stdin)
    sql = build_upsert_sql(payload)
    sys.stdout.write(sql)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""新 GMV 入库脚本

读取 prepare_gmv_combined_to_json.py 输出的 JSON，
生成 shop_daily_key_data.gmv 的 UPDATE SQL。
"""

import json
import sys


def build_upsert_sql(payload: dict) -> str:
    summary = payload.get("summary", {})
    biz_date = summary.get("biz_date", "")
    gmv_total = summary.get("gmv_total", 0)

    return f"""-- 新 GMV（链路1 日历房 + 链路2 度假订单导出）
-- 日期: {biz_date}
-- 链路1 (日历房): {summary.get('chain1_hotel_calendar', 0)}
-- 链路2 (度假订单): {summary.get('chain2_vacation_export', 0)}
-- GMV合计: {gmv_total}

INSERT INTO Xiangwang.shop_daily_key_data (日期, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_daily_key_data
    WHERE 日期 = '{biz_date}'
);

UPDATE Xiangwang.shop_daily_key_data
SET gmv = NULL
WHERE 日期 = '{biz_date}';

UPDATE Xiangwang.shop_daily_key_data
SET gmv = {gmv_total}
WHERE 日期 = '{biz_date}';
"""


def main() -> int:
    payload = json.load(sys.stdin)
    sql = build_upsert_sql(payload)
    sys.stdout.write(sql)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

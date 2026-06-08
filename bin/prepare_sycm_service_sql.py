#!/usr/bin/env python3
"""SYCM 服务数据（咨询人数）入库脚本

读取 prepare_sycm_service_to_json.py 输出的 JSON，
生成 shop_data_daily_registration.咨询人数 的 UPSERT SQL。
"""

import json
import sys


def build_upsert_sql(payload: dict) -> str:
    summary = payload.get("summary", {})
    rows = payload.get("rows", [])

    if not rows:
        return "-- 没有数据需要入库\n"

    biz_date = summary.get("biz_date", "")
    consultation_count = rows[0].get("咨询人数", 0)

    return f"""-- SYCM服务核心监控 → 店铺每日登记.咨询人数
-- 日期: {biz_date}
-- 咨询人数: {consultation_count}

INSERT INTO Xiangwang.shop_data_daily_registration (`日期`, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_data_daily_registration
    WHERE `日期` = '{biz_date}'
);

UPDATE Xiangwang.shop_data_daily_registration
SET `咨询人数` = NULL
WHERE `日期` = '{biz_date}';

UPDATE Xiangwang.shop_data_daily_registration
SET `咨询人数` = {consultation_count}
WHERE `日期` = '{biz_date}';
"""


def main() -> int:
    payload = json.load(sys.stdin)
    sql = build_upsert_sql(payload)
    sys.stdout.write(sql)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

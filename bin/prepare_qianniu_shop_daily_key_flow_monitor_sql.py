#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _to_int_sql(value) -> str:
    if value in (None, ""):
        return "NULL"
    try:
        decimal_value = Decimal(str(value).replace(",", ""))
    except InvalidOperation:
        return "NULL"
    return str(int(decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))


def _biz_date(payload: dict) -> str:
    summary = payload.get("summary") or {}
    biz_date = summary.get("biz_date") or summary.get("date") or summary.get("日期")
    if not biz_date:
        raise ValueError("payload.summary missing biz_date")
    return str(biz_date).split()[0]


def build_update_sql(payload: dict) -> str:
    rows = payload.get("rows") or []
    if len(rows) != 1:
        raise ValueError("flow monitor payload must contain exactly one row")

    biz_date = _biz_date(payload)
    row = rows[0]
    total_pv = _to_int_sql(row.get("浏览量"))
    total_uv = _to_int_sql(row.get("访客数"))
    ad_uv = _to_int_sql(row.get("广告流量"))
    platform_uv = _to_int_sql(row.get("平台流量"))

    return f"""INSERT INTO Xiangwang.shop_daily_key_data (`日期`, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_daily_key_data
    WHERE `日期` = '{biz_date}'
);

UPDATE Xiangwang.shop_daily_key_data
SET total_pv = NULL,
    total_uv = NULL,
    `流量来源广告_uv` = NULL,
    `流量来源平台_uv` = NULL
WHERE `日期` = '{biz_date}';

UPDATE Xiangwang.shop_daily_key_data
SET total_pv = {total_pv},
    total_uv = {total_uv},
    `流量来源广告_uv` = {ad_uv},
    `流量来源平台_uv` = {platform_uv}
WHERE `日期` = '{biz_date}';"""


def main() -> int:
    payload = json.load(sys.stdin)
    sys.stdout.write(build_update_sql(payload))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

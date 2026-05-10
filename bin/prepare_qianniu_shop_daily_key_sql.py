#!/usr/bin/env python3
"""Generate SQL for order summary fields in qianniu daily key data."""

from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _to_decimal(value) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    cleaned = str(value).replace(",", "").strip()
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _format_decimal(value) -> str:
    return str(_to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _format_booking(value) -> str:
    decimal_value = _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if decimal_value == decimal_value.to_integral():
        return str(int(decimal_value))
    return str(decimal_value)


def _summary_date(summary: dict) -> str:
    for key in ("deal_start", "biz_date", "date", "日期"):
        value = summary.get(key)
        if value:
            return str(value).split()[0]
    raise ValueError("summary missing date field: deal_start/biz_date/date")


def _is_all_pages_collected(summary: dict) -> bool:
    total_page = int(summary.get("total_page") or 0)
    return total_page <= 1 or bool(summary.get("all_pages"))


def build_upsert_sql(payload: dict) -> str:
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        raise ValueError("payload.summary must be a mapping")
    if not _is_all_pages_collected(summary):
        raise ValueError("order payload has multiple pages; collect with --all-pages before daily-key import")

    biz_date = _summary_date(summary)
    total_bookings = _format_booking(summary.get("total_booking"))
    total_pax = _format_decimal(summary.get("total_pax"))
    gmv = _format_decimal(summary.get("gmv"))

    return f"""
-- 飞猪订单汇总写入千牛飞猪店铺日度关键数据
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
SET total_bookings = NULL,
    total_pax = NULL,
    gmv = NULL
WHERE 日期 = '{biz_date}';

UPDATE Xiangwang.shop_daily_key_data
SET total_bookings = {total_bookings},
    total_pax = {total_pax},
    gmv = {gmv}
WHERE 日期 = '{biz_date}';
"""


def main() -> int:
    payload = json.load(sys.stdin)
    sys.stdout.write(build_upsert_sql(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

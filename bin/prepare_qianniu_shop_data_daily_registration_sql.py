#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _to_int(value) -> int:
    if value in (None, ""):
        return 0
    try:
        decimal_value = Decimal(str(value).replace(",", ""))
    except InvalidOperation:
        return 0
    return int(decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _extract_record(payload: dict) -> tuple[str, int]:
    if "rows" in payload:
        rows = payload.get("rows") or []
        if not rows:
            raise ValueError("payload.rows must contain at least one row")
        summary = payload.get("summary") or {}
        biz_date = summary.get("biz_date") or summary.get("date") or summary.get("日期")
        row = rows[0]
    else:
        biz_date = payload.get("biz_date") or payload.get("date") or payload.get("日期")
        row = payload

    if not biz_date:
        raise ValueError("payload missing biz_date")
    return str(biz_date).split()[0], _to_int(row.get("关注店铺人数"))


def build_upsert_sql(payload: dict) -> str:
    biz_date, follow_count = _extract_record(payload)
    return f"""INSERT INTO Xiangwang.shop_data_daily_registration (`日期`, created_at)
SELECT '{biz_date}', NOW()
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1
    FROM Xiangwang.shop_data_daily_registration
    WHERE `日期` = '{biz_date}'
);

UPDATE Xiangwang.shop_data_daily_registration
SET `关注店铺人数` = NULL
WHERE `日期` = '{biz_date}';

UPDATE Xiangwang.shop_data_daily_registration
SET `关注店铺人数` = {follow_count}
WHERE `日期` = '{biz_date}';"""


def main() -> int:
    payload = json.load(sys.stdin)
    sys.stdout.write(build_upsert_sql(payload))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


DATE_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})至(\d{4}-\d{2}-\d{2})")
SUMMARY_NAMES = {"汇总", "均值"}


def _extract_biz_date(file_path: str) -> str:
    match = DATE_PATTERN.search(file_path or "")
    if not match:
        raise ValueError("summary.file_path does not contain date range")
    start_date, end_date = match.groups()
    if start_date != end_date:
        raise ValueError("daily customer service payload requires same start and end date")
    return start_date


def _quote_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "''") + "'"


def _to_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _format_decimal(value, quant: str) -> str:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return "NULL"
    return str(decimal_value.quantize(Decimal(quant), rounding=ROUND_HALF_UP))


def _format_int(value) -> str:
    decimal_value = _to_decimal(value)
    if decimal_value is None:
        return "NULL"
    normalized = decimal_value.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return str(int(normalized))


def _format_varchar(value) -> str:
    if value in (None, ""):
        return "NULL"
    return _quote_string(str(value))


def _iter_customer_rows(payload: dict):
    for row in payload.get("rows", []):
        nickname = row.get("客服昵称")
        if not nickname or str(nickname).strip() in SUMMARY_NAMES:
            continue
        yield row


def build_upsert_sql(payload: dict) -> str:
    summary = payload.get("summary") or {}
    if summary.get("report_name") != "人均日接入":
        raise ValueError("summary.report_name must be 人均日接入")

    biz_date = _extract_biz_date(summary.get("file_path", ""))
    values = []
    for row in _iter_customer_rows(payload):
        values.append(
            "("
            + ", ".join(
                [
                    _quote_string(biz_date),
                    _quote_string(str(row.get("客服昵称"))),
                    _format_int(row.get("接待人数")),
                    _format_decimal(row.get("平均响应(秒)"), "0.01"),
                    _format_decimal(row.get("回复率"), "0.000"),
                    _format_decimal(row.get("询单->最终付款转化率"), "0.0000"),
                    _format_decimal(row.get("上班天数"), "0.0"),
                    _format_decimal(row.get("服务满意度评价参与率"), "0.0000"),
                    _format_varchar(row.get("客户满意率")),
                    _format_varchar(row.get("服务满意度评价很满意")),
                    _format_varchar(row.get("服务满意度评价满意")),
                    _format_varchar(row.get("服务满意度评价一般")),
                    _format_varchar(row.get("服务满意度评价不满")),
                    _format_varchar(row.get("服务满意度评价很不满")),
                ]
            )
            + ")"
        )

    if not values:
        return (
            "DELETE FROM Xiangwang.customer_service_data_daily\n"
            f"WHERE `日期` = '{biz_date}';"
        )

    return (
        "DELETE FROM Xiangwang.customer_service_data_daily\n"
        f"WHERE `日期` = '{biz_date}';\n"
        "INSERT INTO Xiangwang.customer_service_data_daily\n"
        "(`日期`, `旺旺`, `接待人数`, `平均响应秒`, `回复率`, `询单最终付款成功率`, `上班天数`, `评价发送率`, `客户满意比`, `很满意`, `满意`, `一般`, `不满意`, `很不满意`)\n"
        "VALUES\n"
        + ",\n".join(values)
        + ";"
    )


def main() -> int:
    payload = json.load(sys.stdin)
    sql = build_upsert_sql(payload)
    sys.stdout.write(sql)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


ROOM_CAPACITY_PATTERN = re.compile(r"(\d+)人房")
CHINESE_ROOM_CAPACITY_PREFIXES = (
    ("单人", 1),
    ("双人", 2),
    ("三人", 3),
    ("四人", 4),
    ("五人", 5),
    ("六人", 6),
)
MONEY_CLEAN_PATTERN = re.compile(r"[^\d.\-]")
# 非通兑订单排除关键词：仅在订单非通兑时才生效
PAX_BK_EXCLUDE_KEYWORDS = (
    "补差", "尾款", "升级", "升房", "升舱",
    "税费", "补税", "改期", "改航线", "生日礼遇",
)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    cleaned = MONEY_CLEAN_PATTERN.sub("", str(value))
    if not cleaned:
        return Decimal("0")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return Decimal("0")


def _extract_room_capacity(package_type: str | None) -> int | None:
    if not package_type:
        return None
    match = ROOM_CAPACITY_PATTERN.search(package_type)
    if match:
        return int(match.group(1))
    for prefix, capacity in CHINESE_ROOM_CAPACITY_PREFIXES:
        if prefix in package_type:
            return capacity
    return None


def _should_skip_pax_bk(row: dict) -> bool:
    """通兑/舱房订单永不算金额订单；仅非舱房订单检查排除关键词"""
    package_type = row.get("package_type") or ""
    if "通兑" in package_type:
        return False
    combined = f'{row.get("item_title") or ""} {package_type}'
    return any(keyword in combined for keyword in PAX_BK_EXCLUDE_KEYWORDS)


def _decimal_to_json_number(value: Decimal):
    normalized = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if normalized == normalized.to_integral():
        return int(normalized)
    return float(normalized)


def prepare_payload_for_storage(payload: dict) -> dict:
    result = deepcopy(payload)
    rows = result.get("rows", result.get("orders", []))

    total_pax = Decimal("0")
    total_booking = Decimal("0")
    gmv = Decimal("0")

    for row in rows:
        package_type = row.get("package_type")
        buy_mount = _to_decimal(row.get("buy_mount"))
        room_capacity = _extract_room_capacity(package_type)
        is_universal = "通兑" in (package_type or "")
        gmv += _to_decimal(row.get("actual_fee"))

        if _should_skip_pax_bk(row):
            continue

        if is_universal and room_capacity:
            total_pax += buy_mount * Decimal(room_capacity)
            total_booking += buy_mount
        elif room_capacity:
            total_pax += buy_mount
            total_booking += buy_mount / Decimal(room_capacity)
        else:
            total_pax += buy_mount
            total_booking += buy_mount

    summary = result.setdefault("summary", {})
    summary["total_pax"] = _decimal_to_json_number(total_pax)
    summary["total_booking"] = _decimal_to_json_number(total_booking)
    summary["gmv"] = _decimal_to_json_number(gmv)
    if "orders" in result and "rows" not in result:
        result["rows"] = result.pop("orders")
    return result


def main() -> int:
    # 支持命令行参数传入JSON文件路径，否则从stdin读取
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)

    result = prepare_payload_for_storage(payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

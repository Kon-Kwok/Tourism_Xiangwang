"""Parse secondary booking order XML and extract order data.

The bookInfoList.htm response is actually XML transformed by XSLT in the browser.
Key XML structure:
  <root><data><list>
    <i>
      <tc-or-num>    订单编号 (A列)
      <title>        商品标题
      <pcount>       数量 (I列 equivalent)
      <status-desc>  订单状态 (K列)
      <sku><i>       套餐类型 (contains 房型标注人数 in Q列)
      <apply-time>   提交时间
      <ptime>        成交时间
      <ttime>        出行日期
      <price>        价格
    </i>
  </list></data></root>
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET

# Status to exclude per SOP
EXCLUDED_STATUS = "商家已驳回"

# Room capacity patterns — 覆盖 Q 列常见写法
# 数字格式："2人房", "4人间", "3人房"
_ROOM_CAPACITY_DIGIT_RE = re.compile(r"(\d+)\s*人[房间]?")
# 中文格式 fallback（与 prepare_order_list_for_storage.py 对齐）
_CHINESE_ROOM_CAPACITY: list[tuple[str, int]] = [
    ("单人", 1), ("双人", 2), ("三人", 3),
    ("四人", 4), ("五人", 5), ("六人", 6),
]


def _extract_room_capacity_from_sku(sku_items: list[str]) -> int | None:
    """从 SKU 文本中提取房型标注人数（Q 列）。

    覆盖：
      - "阳台2人房通兑" → 2
      - "豪华三人间"       → 3
      - "双人阳台房"       → 2
    """
    for item in sku_items:
        # 先尝试数字格式
        match = _ROOM_CAPACITY_DIGIT_RE.search(item)
        if match:
            return int(match.group(1))
        # 再尝试中文格式
        for prefix, capacity in _CHINESE_ROOM_CAPACITY:
            if prefix in item:
                return capacity
    return None


def parse_xml(xml_text: str) -> tuple[list[dict], bool, list[dict]]:
    """Parse the bookInfoList.htm XML and extract order data.

    Args:
        xml_text: Raw XML text from bookInfoList.htm.

    Returns:
        (orders, has_next_page, exceptions) tuple:
          orders: list of order dicts (including 商家已驳回 — filtered at query time)
          has_next_page: True if there may be more pages
          exceptions: list of dicts for orders with unparseable room_capacity
            {order_id, raw_sku_items, buy_mount, status_text, submit_time}
    """
    # Strip XSLT processing instruction and leading whitespace
    # The XML starts with <?xml-stylesheet ...?> then <root>
    root = ET.fromstring(xml_text)

    data = root.find("data")
    if data is None:
        return [], False, []

    list_elem = data.find("list")
    if list_elem is None:
        return [], False, []

    orders = []
    exceptions = []
    for item in list_elem.findall("i"):
        # Order number (A列)
        tc_or_num = _text(item, "tc-or-num")

        # Product title
        title = _text(item, "title")

        # Quantity (I列 equivalent)
        pcount_str = _text(item, "pcount")
        buy_mount = int(pcount_str) if pcount_str else 0

        # Status (K列) — 不在此处过滤，保留全部订单通过 upsert 更新状态
        status_desc = _text(item, "status-desc") or ""

        # Room capacity from SKU (Q列)
        sku_items: list[str] = []
        sku_elem = item.find("sku")
        if sku_elem is not None:
            for sku_i in sku_elem.findall("i"):
                if sku_i.text:
                    sku_items.append(sku_i.text)

        room_capacity = _extract_room_capacity_from_sku(sku_items)

        # Submit time (提交时间)
        apply_time = _text(item, "apply-time")

        # Deal time (成交时间)
        ptime = _text(item, "ptime")

        # Travel date (出行日期)
        ttime = _text(item, "ttime")

        # Price
        price = _text(item, "price")

        # PAX = buy_mount × room_capacity（严格按 SOP，不允许 fallback）
        if room_capacity is None:
            pax = None
            exceptions.append({
                "order_id": tc_or_num,
                "raw_sku_items": sku_items,
                "buy_mount": buy_mount,
                "status_text": status_desc,
                "submit_time": apply_time,
            })
        else:
            pax = buy_mount * room_capacity

        orders.append({
            "order_id": tc_or_num,
            "item_title": title,
            "buy_mount": buy_mount,
            "room_capacity": room_capacity,
            "pax": pax,
            "status_text": status_desc,
            "deal_time": ptime,
            "submit_time": apply_time,
            "travel_date": ttime,
            "price": price,
        })

    # Deduplicate by order_id（SOP: A列去除重复值，按订单编号）
    seen: set[str] = set()
    unique_orders = []
    for o in orders:
        oid = o["order_id"]
        if oid and oid not in seen:
            seen.add(oid)
            unique_orders.append(o)

    # Pagination: page size is ~10 items. If this page returned fewer
    # than 10 raw items, it's the last page.
    raw_item_count = len(list_elem.findall("i"))
    has_next = raw_item_count >= 10

    return unique_orders, has_next, exceptions


def _text(element: ET.Element | None, tag: str) -> str | None:
    """Safely extract text from a child element."""
    if element is None:
        return None
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None

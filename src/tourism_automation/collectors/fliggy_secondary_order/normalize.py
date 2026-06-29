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
import xml.etree.ElementTree as ET

# Status to exclude per SOP
EXCLUDED_STATUS = "商家已驳回"

# Room capacity pattern e.g. "阳台2人房通兑" → 2
ROOM_CAPACITY_RE = re.compile(r"(\d+)人房")


def _extract_room_capacity_from_sku(sku_items: list[str]) -> int | None:
    """Extract room capacity from SKU text like '套餐类型:阳台2人房通兑'."""
    for item in sku_items:
        if "套餐类型" in item:
            match = ROOM_CAPACITY_RE.search(item)
            if match:
                return int(match.group(1))
    return None


def parse_xml(xml_text: str) -> tuple[list[dict], bool]:
    """Parse the bookInfoList.htm XML and extract order data.

    Args:
        xml_text: Raw XML text from bookInfoList.htm.

    Returns:
        (orders, has_next_page) tuple:
          orders: list of order dicts
          has_next_page: True if there may be more pages
    """
    # Strip XSLT processing instruction and leading whitespace
    # The XML starts with <?xml-stylesheet ...?> then <root>
    root = ET.fromstring(xml_text)

    data = root.find("data")
    if data is None:
        return [], False

    size_elem = data.find("size")
    total_size = int(size_elem.text) if size_elem is not None and size_elem.text else 0

    list_elem = data.find("list")
    if list_elem is None:
        return [], False

    orders = []
    for item in list_elem.findall("i"):
        # Order number (A列)
        tc_or_num = _text(item, "tc-or-num")

        # Product title
        title = _text(item, "title")

        # Quantity (I列 equivalent) — pcount = passenger/room count
        pcount_str = _text(item, "pcount")
        buy_mount = int(pcount_str) if pcount_str else 0

        # Status (K列)
        status_desc = _text(item, "status-desc")

        # Filter excluded status
        if status_desc == EXCLUDED_STATUS:
            continue

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

        # PAX = buy_mount × room_capacity per SOP
        pax = buy_mount * (room_capacity or 1)

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

    # Deduplicate by order_id
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

    return unique_orders, has_next


def _text(element: ET.Element | None, tag: str) -> str | None:
    """Safely extract text from a child element."""
    if element is None:
        return None
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None

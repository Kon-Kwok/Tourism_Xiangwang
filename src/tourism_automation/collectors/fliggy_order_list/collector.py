from __future__ import annotations

from tourism_automation.collectors.fliggy_order_list.client import FliggyOrderListClient
from tourism_automation.collectors.fliggy_order_list.normalize import normalize_order_list_payload


MAX_PAGE_SIZE = 20


def collect_order_list(
    *,
    page_num: int,
    page_size: int,
    biz_type: int = 0,
    sort_field_enum: str = "ORDER_CREATE_TIME_DESC",
    deal_start: str,
    deal_end: str,
    all_pages: bool = False,
) -> dict:
    page_size = min(page_size, MAX_PAGE_SIZE)
    client = FliggyOrderListClient.from_local_chrome()
    payload = client.fetch_order_list(
        page_num=page_num,
        page_size=page_size,
        biz_type=biz_type,
        sort_field_enum=sort_field_enum,
        deal_start=deal_start,
        deal_end=deal_end,
    )
    normalized = normalize_order_list_payload(
        payload,
        page_num=page_num,
        page_size=page_size,
        deal_start=deal_start,
        deal_end=deal_end,
    )
    if not all_pages or normalized["summary"]["total_page"] <= 1:
        return normalized

    all_rows = list(normalized["rows"])
    total_page = int(normalized["summary"]["total_page"])
    for next_page in range(page_num + 1, total_page + 1):
        next_payload = client.fetch_order_list(
            page_num=next_page,
            page_size=page_size,
            biz_type=biz_type,
            sort_field_enum=sort_field_enum,
            deal_start=deal_start,
            deal_end=deal_end,
        )
        next_normalized = normalize_order_list_payload(
            next_payload,
            page_num=next_page,
            page_size=page_size,
            deal_start=deal_start,
            deal_end=deal_end,
        )
        all_rows.extend(next_normalized["rows"])

    normalized["rows"] = all_rows
    normalized["summary"]["order_count"] = len(all_rows)
    normalized["summary"]["all_pages"] = True
    normalized["summary"]["page_num"] = page_num
    normalized["summary"]["page_size"] = page_size
    return normalized

#!/usr/bin/env python3
"""新 GMV 采集：链路1（日历房）+ 链路2（度假订单导出），输出 JSON。

链路1: hotel.fliggy.com 日历房订单 → 分页加总 checkOutRoomPrice
链路2: sell.fliggy.com 度假订单导出 → 下载 xls → 排除付款时间空白 → 加总"总金额"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tourism_automation.shared.chrome import ChromeHttpClient


HOTEL_ORDER_API = "https://hotel.fliggy.com/ota/reactjs/order_search.htm"
EXPORT_CREATE_URL = "https://sell.fliggy.com/orderlist/ajax/exportOrderListV2.do?_input_charset=UTF-8&_output_charset=UTF-8"
EXPORT_HISTORY_URL = "https://sell.fliggy.com/orderlist/ajax/exportOrderHistoryList.do?_input_charset=UTF-8&_output_charset=UTF-8"
DOWNLOAD_BASE = "https://sell.fliggy.com/"
FLIGGY_REFERER = "https://fsc.fliggy.com/"


def _get_tb_token(http: ChromeHttpClient) -> str:
    for cookie in http.session.cookies:
        if cookie.name == "_tb_token_":
            return cookie.value
    return http.session.cookies.get("_tb_token_", "")


# ---------- 链路1 ----------

def _collect_hotel_calendar(http: ChromeHttpClient, biz_date: str) -> float:
    """分页获取日历房订单，加总 checkOutRoomPrice"""
    total = 0.0
    page = 1
    page_size = 50

    while True:
        params = {
            "_tb_token_": _get_tb_token(http),
            "paymentType": "0",
            "current": str(page),
            "pageSize": str(page_size),
            "pageIndex": str(page),
            "pageType": "0",
            "createdStart": biz_date,
            "createdEnd": biz_date,
            "packageOrder": "",
            "ajaxSourceFromAsync": "async",
        }
        url = f"{HOTEL_ORDER_API}?{urlencode(params)}"
        resp = http.session.get(url, headers={"Referer": FLIGGY_REFERER}, timeout=30)
        data = resp.json()

        if not data.get("success"):
            raise RuntimeError(f"日历房API失败: {data}")

        order_data = data.get("data", {})
        orders = order_data.get("orderList", [])

        for order in orders:
            try:
                total += float(order.get("checkOutRoomPrice", 0))
            except (ValueError, TypeError):
                pass

        total_page = order_data.get("totalPage", 1)
        if page >= total_page:
            break
        page += 1

    return total


# ---------- 链路2 ----------

def _trigger_export(http: ChromeHttpClient, biz_date: str, token: str):
    """触发度假订单报表导出"""
    deal_range = f"{biz_date} 00:00:00~{biz_date} 23:59:59"
    resp = http.session.post(
        EXPORT_CREATE_URL,
        files=[
            ("_tb_token_", (None, token)),
            ("bizType", (None, "0")),
            ("sortFieldEnum", (None, "ORDER_CREATE_TIME_DESC")),
            ("orderCreateTime", (None, deal_range)),
            ("pageNum", (None, "1")),
            ("pageSize", (None, "10")),
        ],
        headers={"Referer": FLIGGY_REFERER},
        timeout=30,
    )
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"导出触发失败: {data}")
    return data


def _poll_for_download(http: ChromeHttpClient, biz_date: str, token: str) -> str:
    """轮询导出历史列表，返回最新匹配日期的下载 URL"""
    for attempt in range(15):
        time.sleep(2)
        resp = http.session.post(
            EXPORT_HISTORY_URL,
            files=[
                ("_tb_token_", (None, token)),
                ("pageNum", (None, "1")),
                ("pageSize", (None, "10")),
            ],
            headers={"Referer": FLIGGY_REFERER},
            timeout=30,
        )
        data = resp.json()
        conditions = data.get("result", {}).get("conditions", [])

        for cond in conditions:
            if cond.get("exportStatus") != 1:
                continue
            for item in cond.get("reportList", []):
                if item.get("label") == "成交时间" and biz_date in str(item.get("value", "")):
                    btn = cond.get("buttonGroup", [{}])[0]
                    url = btn.get("url", "")
                    if url:
                        return url

    raise RuntimeError("轮询超时：未找到已生成的导出报表")


def _download_and_calculate(http: ChromeHttpClient, download_url: str, biz_date: str) -> tuple:
    """下载 xls 文件，排除付款时间为空，加总 '总金额'"""
    full_url = f"{DOWNLOAD_BASE}{download_url}"
    resp = http.session.get(full_url, headers={"Referer": FLIGGY_REFERER}, timeout=60)

    tmp_path = Path(tempfile.gettempdir()) / f"vacation_export_{biz_date}.xls"
    tmp_path.write_bytes(resp.content)

    import xlrd
    wb = xlrd.open_workbook(str(tmp_path))
    ws = wb.sheet_by_index(0)
    headers = [ws.cell_value(0, c) for c in range(ws.ncols)]

    amount_col = headers.index("总金额")
    pay_time_col = headers.index("付款时间")

    total = 0.0
    blank_count = 0
    total_count = ws.nrows - 1

    for r in range(1, ws.nrows):
        pay_time = str(ws.cell_value(r, pay_time_col)).strip()
        amount_str = str(ws.cell_value(r, amount_col)).strip()
        try:
            amount = float(re.sub(r"[^\d.\-]", "", amount_str))
        except (ValueError, TypeError):
            continue

        if not pay_time:
            blank_count += 1
            continue
        total += amount

    tmp_path.unlink(missing_ok=True)
    return total, total_count, blank_count


def _collect_vacation_export(http: ChromeHttpClient, biz_date: str) -> tuple:
    """链路2: 触发导出 → 轮询 → 下载 → 加总"""
    token = _get_tb_token(http)
    _trigger_export(http, biz_date, token)
    download_url = _poll_for_download(http, biz_date, token)
    return _download_and_calculate(http, download_url, biz_date)


# ---------- main ----------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="采集新 GMV（链路1+链路2）")
    parser.add_argument("--date", required=True, help="业务日期 YYYY-MM-DD")
    args = parser.parse_args(argv)

    http = ChromeHttpClient.from_local_chrome()

    # 链路1
    chain1 = _collect_hotel_calendar(http, args.date)
    print(f"链路1 (日历房 checkoutRoomPrice):          {chain1:.2f}", file=sys.stderr)

    # 链路2
    chain2, chain2_total, chain2_blank = _collect_vacation_export(http, args.date)
    print(f"链路2 (度假订单, 排除付款时间空白): {chain2:.2f}  "
          f"(共{chain2_total}条, 排除{chain2_blank}条)", file=sys.stderr)

    total_gmv = chain1 + chain2
    print(f"GMV合计 = {chain1:.2f} + {chain2:.2f} = {total_gmv:.2f}", file=sys.stderr)

    payload = {
        "summary": {
            "biz_date": args.date,
            "metric_source": "gmv_combined",
            "chain1_hotel_calendar": round(chain1, 2),
            "chain2_vacation_export": round(chain2, 2),
            "gmv_total": round(total_gmv, 2),
        },
        "rows": [{"gmv": round(total_gmv, 2)}],
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

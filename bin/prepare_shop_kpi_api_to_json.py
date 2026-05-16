#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tourism_automation.shared import CdpClient


DELAY_VALUE = "延迟统计"
REPORT_IDS = {
    "人均日接入": "1721",
    "每周店铺个人数据": "1996",
    "客服数据23年新": "2496",
}
REPORT_MAPPINGS = {
    "人均日接入": {
        "客服昵称": "show_name",
        "接待人数": "service_buyer_num",
        "平均响应(秒)": "avg_total_reply_cost",
        "回复率": "reply_percent",
        "询单->最终付款转化率": "ask_today_final_paid_succrate",
        "上班天数": "work_days",
        "服务满意度评价参与率": "new_eval_receive_rate",
        "客户满意率": "new_customer_satisfied_rate",
        "服务满意度评价很满意": "new_very_satisfied_num",
        "服务满意度评价满意": "new_satisfied_num",
        "服务满意度评价一般": "new_general_num",
        "服务满意度评价不满": "new_dissatisfied_num",
        "服务满意度评价很不满": "new_very_dissatisfied_num",
    },
    "每周店铺个人数据": {
        "客服昵称": "show_name",
        "聊天人数(原咨询人数)": "all_chat_buyer_num",
        "接待人数": "service_buyer_num",
        "询单人数": "ask_num",
        "销售额": "employee_payments_with_deduct",
        "销售量": "employee_item_num_with_deduct",
        "销售人数": "employee_paid_num",
        "销售订单数": "employee_trade_num",
    },
    "客服数据23年新": {
        "客服昵称": "show_name",
        "聊天人数(原咨询人数)": "all_chat_buyer_num",
        "接待人数": "service_buyer_num",
        "直接接入人数": "service_direct_buyer_num",
        "转发接入人数": "service_in_buyer_num",
        "转出人数": "service_out_buyer_num",
        "总消息数": "total_message_num",
        "买家消息数": "buyer_message_num",
        "客服消息数": "seller_message_num",
        "答问比": "seller_buyer_message_percent",
        "客服字数": "waitor_word_num",
        "最大同时聊天数": "max_concurrent_reception_buyer_num",
        "未回复人数": "no_reply_chatpeer_num",
        "回复率": "reply_percent",
        "慢接待人数": "slow_reception_chatpeer_num",
        "长接待人数": "long_receive_chatpeer_num",
        "首次响应(秒)": "avg_first_reply_cost",
        "平均响应(秒)": "avg_total_reply_cost",
        "平均接待时长": "extra_avg_total_reception_cost_chart",
    },
}


def _fetch_report(cdp: CdpClient, report_id: str, biz_date: str) -> dict:
    tab = cdp.find_tab_by_url_pattern("topchitu.com")
    params = {
        "dateType": "dateRange",
        "range": json.dumps({"from": biz_date, "to": biz_date}, separators=(",", ":")),
        "from": biz_date,
        "to": biz_date,
        "queryDateType": "DAY",
        "filterDays": "",
        "exportType": "CUSTOM_WW_KPI",
        "showDelayData": "false",
        "kpiType": "ww",
        "reportId": report_id,
        "handleSubmit": "true",
    }
    url = "https://kf.topchitu.com/api/custom/report/kpi?" + urlencode(params)
    js_code = f"""
    (async () => {{
        const response = await fetch({json.dumps(url)}, {{
            headers: {{ "Accept": "application/json" }}
        }});
        const text = await response.text();
        let data;
        try {{
            data = JSON.parse(text);
        }} catch (error) {{
            return {{ success: false, status: response.status, error: text.slice(0, 500) }};
        }}
        return {{ success: response.ok, status: response.status, data }};
    }})()
    """
    result = cdp.execute_js(tab["ws_url"], js_code, timeout=30)
    if not result.get("success"):
        raise RuntimeError(f"赤兔报表接口请求失败: status={result.get('status')} error={result.get('error')}")
    return result.get("data") or {}


def _coerce_value(item: dict, api_field: str):
    value = item.get(api_field)
    if value is None and api_field in set(item.get("delay_fields") or []):
        return DELAY_VALUE
    if value is None:
        return ""
    return value


def build_payload(api_data: dict, report_name: str, biz_date: str) -> dict:
    if report_name not in REPORT_MAPPINGS:
        supported = ", ".join(REPORT_MAPPINGS)
        raise ValueError(f"不支持的报表名称: {report_name}; 支持: {supported}")

    mapping = REPORT_MAPPINGS[report_name]
    rows = []
    for item in api_data.get("valueList", []):
        row = {
            output_field: _coerce_value(item, api_field)
            for output_field, api_field in mapping.items()
        }
        rows.append(row)

    return {
        "summary": {
            "source": "topchitu_api",
            "report_name": report_name,
            "file_path": f"/topchitu-api/自定义报表_{report_name}_下单优先判定_{biz_date}至{biz_date}.json",
            "row_count": len(rows),
        },
        "rows": rows,
        "raw_summary": {
            "fields": api_data.get("fields", []),
            "customReportFields": api_data.get("customReportFields", []),
            "originReportFields": api_data.get("originReportFields", []),
            "sumMap": api_data.get("sumMap", {}),
            "avgMap": api_data.get("avgMap", {}),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-name", required=True, choices=tuple(REPORT_IDS))
    parser.add_argument("--date", required=True)
    parser.add_argument("--debug-port", type=int, default=9222)
    args = parser.parse_args(argv)

    cdp = CdpClient(debug_port=args.debug_port, default_timeout=30)
    api_data = _fetch_report(cdp, REPORT_IDS[args.report_name], args.date)
    payload = build_payload(api_data, args.report_name, args.date)
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

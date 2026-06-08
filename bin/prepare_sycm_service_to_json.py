#!/usr/bin/env python3
"""从 SYCM 服务核心监控页面采集咨询人数

调用 /csp/api/core/monitor/overview/list 接口，
提取 key=cstUv1d（咨询人数）字段，输出 JSON 供下游 SQL 脚本使用。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tourism_automation.shared.chrome import ChromeHttpClient


SERVICE_API_URL = "https://sycm.taobao.com/csp/api/core/monitor/overview/list"
SERVICE_PAGE_URL = "https://sycm.taobao.com/qos/service/core_monitor/new"


def fetch_service_data(biz_date: str) -> dict:
    """调用 SYCM 服务核心监控 API，返回完整 JSON 响应"""
    http = ChromeHttpClient.from_local_chrome()
    biz_date_compact = biz_date.replace("-", "")
    params = {
        "dateType": "day",
        "dateRange": "1d",
        "endDate": biz_date_compact,
        "excludeDates": "",
        "startDate": biz_date_compact,
    }
    url = f"{SERVICE_API_URL}?{urlencode(params)}"
    return http.fetch_json(url, referer=SERVICE_PAGE_URL)


def extract_consultation_count(api_data: dict) -> int:
    """从 API 响应中提取 咨询人数（cstUv1d）"""
    data_list = api_data.get("data", {}).get("data", [])
    for item in data_list:
        if isinstance(item, dict) and item.get("key") == "cstUv1d":
            return int(item.get("value", 0))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="采集 SYCM 服务核心监控数据")
    parser.add_argument("--date", required=True, help="业务日期 YYYY-MM-DD")
    args = parser.parse_args(argv)

    api_data = fetch_service_data(args.date)
    consultation_count = extract_consultation_count(api_data)

    payload = {
        "summary": {
            "biz_date": args.date,
            "metric_source": "sycm_service_core_monitor",
            "metric_key": "cstUv1d",
        },
        "rows": [
            {"咨询人数": consultation_count}
        ],
    }
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

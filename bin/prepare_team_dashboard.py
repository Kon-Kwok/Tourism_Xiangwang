#!/usr/bin/env python3
"""从赤兔 team-kpi API 采集首次响应时间和平均响应时间并入库。

使用方式:
    python3 bin/prepare_team_dashboard.py --date 2026-06-24
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from tourism_automation.shared.cdp_client import CdpClient


def _read_env() -> dict:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    result = {}
    if not env_path.exists():
        return result
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def connect_db():
    env = _read_env()
    return pymysql.connect(
        host=env.get("HOST", "127.0.0.1"),
        port=int(env.get("PORT", 3306)),
        user=env.get("USER", "root"),
        password=env.get("PASS", ""),
        database="Xiangwang",
        charset="utf8mb4",
    )


def fetch_day(cdp: CdpClient, ws_url: str, biz_date: str) -> dict:
    """Fetch team-kpi API for a single day via CDP (uses browser auth cookies)."""
    js = f"""
    (async () => {{
        const resp = await fetch(
            '/api/homepage/team/team-kpi?from={biz_date}&to={biz_date}&queryDateType=DAY'
        );
        if (!resp.ok) {{
            return JSON.stringify({{error: 'HTTP ' + resp.status}});
        }}
        const data = await resp.json();
        const list = data.valueList || [];
        if (list.length === 0) {{
            return JSON.stringify({{error: 'No data for {biz_date}'}});
        }}
        const r = list[0];
        return JSON.stringify({{
            business_day: r.business_day,
            avg_first_reply_cost: r.avg_first_reply_cost,
            avg_total_reply_cost: r.avg_total_reply_cost
        }});
    }})()
    """
    result = cdp.execute_js(ws_url, js, timeout=20)
    if isinstance(result, str):
        result = json.loads(result)
    return result


def store(conn, biz_date: str, first_sec: float, avg_sec: float):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO Xiangwang.team_dashboard_daily "
            "(date_time, first_response_sec, avg_response_sec) "
            "VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "first_response_sec = VALUES(first_response_sec), "
            "avg_response_sec = VALUES(avg_response_sec)",
            (biz_date, first_sec, avg_sec),
        )
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="采集赤兔团队看板数据")
    parser.add_argument("--date", required=True, help="业务日期 YYYY-MM-DD")
    args = parser.parse_args()

    cdp = CdpClient()
    tab = cdp.find_tab_by_url_pattern("topchitu")
    ws_url = tab["ws_url"]

    data = fetch_day(cdp, ws_url, args.date)
    if "error" in data:
        print(f"ERROR: {data['error']}", file=sys.stderr)
        sys.exit(1)

    first_sec = float(data["avg_first_reply_cost"])
    avg_sec = float(data["avg_total_reply_cost"])

    conn = connect_db()
    try:
        store(conn, args.date, first_sec, avg_sec)
        print(f"采集完成: date={args.date}, "
              f"first_response={first_sec}s, avg_response={avg_sec}s")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

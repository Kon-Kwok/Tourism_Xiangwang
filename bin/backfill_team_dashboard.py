#!/usr/bin/env python3
"""Backfill team_dashboard_daily from 赤兔 team-kpi API.

Usage: python3 bin/backfill_team_dashboard.py --start 2026-06-01 --end 2026-06-24
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from tourism_automation.shared.cdp_client import CdpClient


def _read_env_file() -> dict:
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
    env = _read_env_file()
    return pymysql.connect(
        host=env.get("HOST", "127.0.0.1"),
        port=int(env.get("PORT", 3306)),
        user=env.get("USER", "root"),
        password=env.get("PASS", ""),
        database="Xiangwang",
        charset="utf8mb4",
    )


def fetch_team_kpi(cdp: CdpClient, ws_url: str, start: str, end: str) -> list[dict]:
    """Fetch team-kpi API via CDP (uses browser cookies for auth)."""
    js = f"""
    (async () => {{
        const resp = await fetch(
            '/api/homepage/team/team-kpi?from={start}&to={end}&queryDateType=DAY'
        );
        if (!resp.ok) {{
            return JSON.stringify({{error: 'HTTP ' + resp.status}});
        }}
        const data = await resp.json();
        return JSON.stringify(data);
    }})()
    """
    result = cdp.execute_js(ws_url, js, timeout=20)
    if isinstance(result, str):
        result = json.loads(result)
    if "error" in result:
        raise RuntimeError(result["error"])
    return result.get("valueList", [])


def store_batch(conn, records: list[dict]):
    with conn.cursor() as cur:
        count = 0
        for r in records:
            biz_date = r.get("business_day")
            first_sec = r.get("avg_first_reply_cost")
            avg_sec = r.get("avg_total_reply_cost")
            if not biz_date or first_sec is None or avg_sec is None:
                continue
            cur.execute(
                "INSERT INTO Xiangwang.team_dashboard_daily "
                "(date_time, first_response_sec, avg_response_sec) "
                "VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE "
                "first_response_sec = VALUES(first_response_sec), "
                "avg_response_sec = VALUES(avg_response_sec)",
                (biz_date, float(first_sec), float(avg_sec)),
            )
            count += 1
    conn.commit()
    print(f"Stored {count} records")


def main():
    parser = argparse.ArgumentParser(description="Backfill 赤兔团队看板数据")
    parser.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    args = parser.parse_args()

    cdp = CdpClient()
    tab = cdp.find_tab_by_url_pattern("topchitu")
    ws_url = tab["ws_url"]

    records = fetch_team_kpi(cdp, ws_url, args.start, args.end)
    if not records:
        print("No records returned from API", file=sys.stderr)
        sys.exit(1)

    print(f"Fetched {len(records)} days from API ({args.start} to {args.end})")

    conn = connect_db()
    try:
        store_batch(conn, records)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

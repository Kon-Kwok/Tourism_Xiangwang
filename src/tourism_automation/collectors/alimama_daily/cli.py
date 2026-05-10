"""CLI for Alimama daily advertising reports."""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal

from tourism_automation.collectors.alimama_daily.collector import collect_alimama_daily
from tourism_automation.collectors.alimama_daily.storage import AlimamaDailyStorage


def register_subparser(subparsers):
    parser = subparsers.add_parser("alimama-daily", help="Alimama daily advertising report collector")
    collect = parser.add_subparsers(dest="alimama_daily_command", required=True).add_parser(
        "collect", help="Collect and save Alimama daily reports"
    )
    collect.add_argument("--date", required=True, help="Business date (YYYY-MM-DD)")
    collect.add_argument("--save", action="store_true", help="Save to MySQL")
    collect.add_argument("--mysql-host", default=os.environ.get("HOST", "127.0.0.1"))
    collect.add_argument("--mysql-port", type=int, default=int(os.environ.get("PORT", "3306")))
    collect.add_argument("--mysql-user", default=os.environ.get("MYSQL_USER", os.environ.get("DB_USER", "remote_user")))
    collect.add_argument("--mysql-password", default=os.environ.get("PASS", ""))
    collect.add_argument("--mysql-database", default=os.environ.get("MYSQL_DATABASE", "Xiangwang"))
    collect.add_argument("--json", action="store_true", help="Print full JSON output")
    collect.add_argument("--omit-raw", action="store_true", help="Omit raw payload from output")
    parser.set_defaults(handler=run)


def run(args) -> int:
    if args.alimama_daily_command != "collect":
        return 1
    datetime.strptime(args.date, "%Y-%m-%d")
    result = collect_alimama_daily(biz_date=args.date)
    if args.save:
        storage = AlimamaDailyStorage(
            config={
                "host": args.mysql_host,
                "port": args.mysql_port,
                "user": args.mysql_user,
                "password": args.mysql_password,
                "database": args.mysql_database,
                "charset": "utf8mb4",
            }
        )
        result["saved"] = storage.save(result)
    if args.omit_raw:
        result.pop("raw", None)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))
    else:
        print(_summary_text(result))
    return 0


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _summary_text(result: dict) -> str:
    lines = [
        "阿里妈妈投放日报采集完成",
        f"日期：{result['date_time']}",
        f"状态：{result['status']}",
    ]
    channels = result.get("channels", {})
    channel_labels = [
        ("star_store", "明星店铺"),
        ("tmall_express", "直通车"),
        ("gravity_rubiks_cube", "引力魔方"),
        ("wanxiangtai", "万相台"),
    ]
    for key, label in channel_labels:
        metrics = channels.get(key)
        if metrics:
            lines.append(
                f"{label}：花费 {metrics['cost']}，展示 {metrics['imp']}，点击 {metrics['click']}，订单 {metrics['order_count']}"
            )
        else:
            lines.append(f"{label}：未采集到")
    wanxiangtai_2_rows = result.get("wanxiangtai_2_rows", {})
    if wanxiangtai_2_rows:
        lines.append(f"万相台2：{len(wanxiangtai_2_rows)} 行（含小计）")
    missing = result.get("missing_channels") or []
    if missing:
        lines.append(f"缺失：{', '.join(missing)}")
    saved = result.get("saved")
    if saved:
        saved_tables = [table for table, ok in saved.items() if ok]
        lines.append(f"入库：{', '.join(saved_tables)}")
    return "\n".join(lines)

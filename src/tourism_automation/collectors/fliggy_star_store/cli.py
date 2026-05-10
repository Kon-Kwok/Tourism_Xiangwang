"""CLI for the Fliggy star store report collector."""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal

from tourism_automation.collectors.fliggy_star_store.collector import collect_star_store
from tourism_automation.collectors.fliggy_star_store.storage import FliggyStarStoreStorage


def register_subparser(subparsers):
    parser = subparsers.add_parser("fliggy-star-store", help="Fliggy Alimama star store report collector")
    star_subparsers = parser.add_subparsers(dest="star_store_command", required=True)

    collect = star_subparsers.add_parser("collect", help="Collect star store report for one date")
    collect.add_argument("--date", required=True, help="Business date (YYYY-MM-DD)")
    collect.add_argument("--save", action="store_true", help="Save to Xiangwang.star_store")
    collect.add_argument("--mysql-host", default=os.environ.get("HOST", "127.0.0.1"))
    collect.add_argument("--mysql-port", type=int, default=int(os.environ.get("PORT", "3306")))
    collect.add_argument("--mysql-user", default=os.environ.get("MYSQL_USER", os.environ.get("DB_USER", "remote_user")))
    collect.add_argument("--mysql-password", default=os.environ.get("PASS", ""))
    collect.add_argument("--mysql-database", default=os.environ.get("MYSQL_DATABASE", "Xiangwang"))
    collect.add_argument("--omit-raw", action="store_true", help="Omit raw API payload from CLI output")

    parser.set_defaults(handler=run)


def run(args) -> int:
    if args.star_store_command != "collect":
        return 1

    datetime.strptime(args.date, "%Y-%m-%d")
    result = collect_star_store(biz_date=args.date)
    if args.save and result.get("status") == "success":
        storage = FliggyStarStoreStorage(
            config={
                "host": args.mysql_host,
                "port": args.mysql_port,
                "user": args.mysql_user,
                "password": args.mysql_password,
                "database": args.mysql_database,
                "charset": "utf8mb4",
            }
        )
        row_id = storage.save(result)
        result["saved"] = row_id is not None
        result["id"] = row_id
    elif args.save:
        result["saved"] = False

    if args.omit_raw:
        result.pop("raw", None)

    print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))
    return 0


def _json_default(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

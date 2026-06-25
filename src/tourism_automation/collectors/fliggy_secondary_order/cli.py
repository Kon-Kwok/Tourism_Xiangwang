"""CLI command registration for fliggy-secondary-order collector."""

from __future__ import annotations

import json

from tourism_automation.collectors.fliggy_secondary_order.collector import (
    collect_and_store,
)


def register_subparser(subparsers):
    parser = subparsers.add_parser(
        "fliggy-secondary-order",
        help="Fliggy secondary booking order collector",
    )
    collector_subparsers = parser.add_subparsers(
        dest="collector_command", required=True
    )

    list_parser = collector_subparsers.add_parser(
        "collect",
        help="Collect secondary booking orders for a date range",
    )
    list_parser.add_argument(
        "--start-date",
        required=True,
        help="Start date, format YYYY-MM-DD (e.g. 2026-06-01)",
    )
    list_parser.add_argument(
        "--end-date",
        required=True,
        help="End date, format YYYY-MM-DD (e.g. 2026-06-30)",
    )
    list_parser.add_argument(
        "--output",
        "-o",
        help="Optional JSON output file path",
    )

    parser.set_defaults(handler=run)


def run(args) -> int:
    if args.collector_command == "collect":
        result = collect_and_store(
            start_date=args.start_date,
            end_date=args.end_date,
            output=args.output,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return 1

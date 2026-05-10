"""Unified CLI entrypoint for collectors."""

from __future__ import annotations

import argparse
import json

from tourism_automation.collectors.fliggy_home.cli import register_subparser as register_fliggy_home_subparser
from tourism_automation.collectors.alimama_daily.cli import register_subparser as register_alimama_daily_subparser
from tourism_automation.collectors.fliggy_kpi.employee_kpi.cli import register_subparser as register_fliggy_kpi_subparser
from tourism_automation.collectors.fliggy_kpi.shop_kpi.cli import register_subparser as register_shop_kpi_export
from tourism_automation.collectors.fliggy_order_list.cli import register_subparser as register_fliggy_order_list_subparser
from tourism_automation.collectors.fliggy_star_store.cli import register_subparser as register_fliggy_star_store_subparser
from tourism_automation.collectors.sycm.cli import register_subparser as register_sycm_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tourism automation collectors")
    subparsers = parser.add_subparsers(dest="collector", required=True)

    register_sycm_subparser(subparsers)
    register_fliggy_home_subparser(subparsers)
    register_alimama_daily_subparser(subparsers)
    register_fliggy_kpi_subparser(subparsers)
    register_fliggy_order_list_subparser(subparsers)
    register_fliggy_star_store_subparser(subparsers)
    register_shop_kpi_export(subparsers)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return args.handler(args)
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

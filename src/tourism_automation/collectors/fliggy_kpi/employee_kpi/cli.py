"""飞猪客服KPI CLI集成"""

from __future__ import annotations

import json

from tourism_automation.collectors.fliggy_kpi.employee_kpi.collector import EmployeeKpiCollector
from tourism_automation.collectors.fliggy_kpi.employee_kpi.storage import EmployeeKpiStorage


def register_subparser(subparsers):
    """注册飞猪客服KPI子命令"""
    parser = subparsers.add_parser("fliggy-kpi", help="Fliggy customer service KPI data collection")
    kpi_subparsers = parser.add_subparsers(dest="kpi_command", required=True)

    # 员工KPI采集命令
    employee_kpi = kpi_subparsers.add_parser("employee", help="Collect employee KPI data")
    employee_kpi.add_argument("--date", required=True, help="Business date (YYYY-MM-DD)")
    employee_kpi.add_argument("--shop-name", default="default", help="Shop name")
    employee_kpi.add_argument("--kpi-id", default="1721", help="KPI template ID")
    employee_kpi.add_argument("--wwt", default="ALL", help="Time range type")
    employee_kpi.add_argument("--method", default="api", choices=["api", "cdp", "http"], help="Collection method: api (via CDP fetch), http (pure HTTP with cached auth), or cdp (table extraction)")
    employee_kpi.add_argument("--save", action="store_true", help="Save to database")

    # 员工KPI导出命令
    employee_export = kpi_subparsers.add_parser("export", help="Export employee KPI data file")
    employee_export.add_argument("--date", required=True, help="Business date (YYYY-MM-DD)")
    employee_export.add_argument("--password", default="1234", help="Export password (default: 1234)")
    employee_export.add_argument("--kpi-id", default="1721", help="KPI template ID")
    employee_export.add_argument("--wwt", default="ALL", help="Time range type")
    employee_export.add_argument("--output-dir", default="/tmp", help="Output directory for downloaded file")

    parser.set_defaults(handler=run)


def run(args) -> int:
    """处理飞猪客服KPI命令"""
    if args.kpi_command == "employee":
        try:
            # 根据method选择采集器
            if args.method == "http":
                from tourism_automation.collectors.fliggy_kpi.employee_kpi.http_collector import EmployeeKpiHttpCollector
                collector = EmployeeKpiHttpCollector()
            elif args.method == "api":
                from tourism_automation.collectors.fliggy_kpi.employee_kpi.api_collector import EmployeeKpiApiCollector
                collector = EmployeeKpiApiCollector()
            else:
                collector = EmployeeKpiCollector()

            # 采集数据
            result = collector.collect(
                biz_date=args.date,
                shop_name=args.shop_name,
                kpi_id=args.kpi_id,
                wwt=args.wwt
            )

            # 如果需要保存到数据库
            if args.save:
                storage = EmployeeKpiStorage(config={"host": "localhost", "user": "root", "database": "Xiangwang"})
                storage.ensure_schema()
                batch_id = storage.save(result)
                result["batch_id"] = batch_id
                result["saved"] = True

            # 输出结果
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

        except Exception as exc:
            error_result = {
                "status": "error",
                "error": str(exc),
                "args": {
                    "date": args.date,
                    "shop_name": args.shop_name,
                    "kpi_id": args.kpi_id,
                    "wwt": args.wwt,
                    "method": args.method
                }
            }
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            return 1

    if args.kpi_command == "export":
        try:
            collector = EmployeeKpiCollector()
            result = collector.export(
                biz_date=args.date,
                password=args.password,
                kpi_id=args.kpi_id,
                wwt=args.wwt,
                output_dir=args.output_dir
            )

            # 输出结果
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("status") == "success" else 1

        except Exception as exc:
            error_result = {
                "status": "error",
                "error": str(exc),
                "args": {
                    "date": args.date,
                    "password": "***",  # 隐藏密码
                    "kpi_id": args.kpi_id,
                    "wwt": args.wwt,
                    "output_dir": args.output_dir
                }
            }
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            return 1

    return 1

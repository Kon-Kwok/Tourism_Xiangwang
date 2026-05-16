"""SYCM店铺来源CLI集成"""

from __future__ import annotations

import json

from tourism_automation.collectors.sycm.shop_source.collector import ShopSourceCollector
from tourism_automation.collectors.sycm.shop_source.storage import ShopSourceStorage
from tourism_automation.shared.chrome import ChromeHttpClient


def register_subparser(subparsers):
    """注册店铺来源子命令"""
    # 在现有的sycm解析器下添加shop-source子命令
    shop_source_subparsers = subparsers.add_subparsers(dest="shop_source_command", required=True)

    # 采集命令
    collect = shop_source_subparsers.add_parser("collect", help="采集店铺来源数据")
    collect.add_argument("--date", required=True, help="业务日期 (YYYY-MM-DD)")
    collect.add_argument("--shop-name", default="default", help="店铺名称")
    collect.add_argument("--active-key", default="item", help="活动类型 (item=商品)")
    collect.add_argument("--belong", default="all", help="归类 (all=全部)")
    collect.add_argument("--device", default="2", help="设备类型 (2=无线, 1=PC, 0=全部)")
    collect.add_argument("--save", action="store_true", help="保存到数据库")


def run(args) -> int:
    """处理店铺来源命令"""
    if args.shop_source_command == "collect":
        try:
            # 采集数据
            collector = ShopSourceCollector(http=ChromeHttpClient.from_local_chrome())
            result = collector.collect(
                biz_date=args.date,
                shop_name=args.shop_name
            )

            # 如果需要保存到数据库
            if args.save:
                storage = ShopSourceStorage(config={"host": "localhost", "user": "root", "database": "Xiangwang"})
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
                    "active_key": args.active_key,
                    "belong": args.belong,
                    "device": args.device
                }
            }
            print(json.dumps(error_result, ensure_ascii=False, indent=2))
            return 1

    return 1

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_qianniu_shop_daily_key_flow_monitor_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_qianniu_shop_daily_key_flow_monitor_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareQianniuShopDailyKeyFlowMonitorSqlTests(unittest.TestCase):
    def test_build_update_sql_maps_flow_monitor_fields(self):
        payload = {
            "summary": {
                "biz_date": "2026-04-20",
                "row_count": 1,
            },
            "rows": [
                {
                    "访客数": 13653,
                    "浏览量": 31835,
                    "广告流量": 10510,
                    "平台流量": 4030,
                }
            ],
        }

        sql = MODULE.build_update_sql(payload)

        self.assertIn("UPDATE Xiangwang.shop_daily_key_data", sql)
        self.assertIn("total_pv = 31835", sql)
        self.assertIn("total_uv = 13653", sql)
        self.assertIn("`流量来源广告_uv` = 10510", sql)
        self.assertIn("`流量来源平台_uv` = 4030", sql)
        self.assertIn("SET total_pv = NULL", sql)
        self.assertIn("WHERE NOT EXISTS", sql)

    def test_build_update_sql_rejects_non_single_row_payload(self):
        payload = {
            "summary": {"biz_date": "2026-04-20"},
            "rows": [],
        }

        with self.assertRaises(ValueError):
            MODULE.build_update_sql(payload)

    def test_main_reads_stdin_and_writes_sql(self):
        payload = {
            "summary": {"biz_date": "2026-04-20"},
            "rows": [
                {
                    "访客数": 13653,
                    "浏览量": 31835,
                    "广告流量": 10510,
                    "平台流量": 4030,
                }
            ],
        }
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("total_pv = 31835", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

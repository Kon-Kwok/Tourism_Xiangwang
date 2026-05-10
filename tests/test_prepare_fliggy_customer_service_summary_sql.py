import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_fliggy_customer_service_summary_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_fliggy_customer_service_summary_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareFliggyCustomerServiceSummarySqlTests(unittest.TestCase):
    def test_build_upsert_sql_filters_summary_rows_and_maps_fields(self):
        payload = {
            "summary": {
                "report_name": "每周店铺个人数据",
                "file_path": "/home/kk/下载/自定义报表_每周店铺个人数据_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "melissa",
                    "聊天人数(原咨询人数)": 98.0,
                    "接待人数": 82.0,
                    "询单人数": "",
                    "销售额": 83263.0,
                    "销售量": 23.0,
                    "销售人数": 4.0,
                    "销售订单数": 8.0,
                },
                {"客服昵称": "汇总", "聊天人数(原咨询人数)": 173.0},
                {"客服昵称": "均值", "聊天人数(原咨询人数)": 14.42},
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("INSERT INTO Xiangwang.customer_service_performance_summary", sql)
        self.assertIn("('melissa', 98, 82, NULL, 83263.00, 23, 4, 8, '2026-04-20')", sql)
        self.assertNotIn("'汇总'", sql)
        self.assertNotIn("'均值'", sql)
        self.assertIn("WHERE `date_time` = '2026-04-20'", sql)

    def test_main_reads_stdin_and_writes_sql(self):
        payload = {
            "summary": {
                "report_name": "每周店铺个人数据",
                "file_path": "/home/kk/下载/自定义报表_每周店铺个人数据_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "james",
                    "聊天人数(原咨询人数)": 75.0,
                    "接待人数": 61.0,
                    "询单人数": "",
                    "销售额": 49728.0,
                    "销售量": 12.0,
                    "销售人数": 5.0,
                    "销售订单数": 5.0,
                }
            ],
        }
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("'james'", stdout.getvalue())
        self.assertIn("49728.00", stdout.getvalue())
        self.assertIn("INSERT INTO Xiangwang.customer_service_performance_summary", stdout.getvalue())

    def test_build_upsert_sql_deletes_day_when_report_is_empty(self):
        payload = {
            "summary": {
                "report_name": "每周店铺个人数据",
                "file_path": "/home/kk/下载/自定义报表_每周店铺个人数据_下单优先判定_2026-04-21至2026-04-21.xlsx",
            },
            "rows": [],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertEqual(
            sql,
            "DELETE FROM Xiangwang.customer_service_performance_summary\n"
            "WHERE date_time = '2026-04-21';",
        )


if __name__ == "__main__":
    unittest.main()

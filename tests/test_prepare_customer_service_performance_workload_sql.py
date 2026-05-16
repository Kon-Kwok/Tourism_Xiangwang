import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_customer_service_performance_workload_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_customer_service_performance_workload_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareCustomerServicePerformanceWorkloadSqlTests(unittest.TestCase):
    def test_build_upsert_sql_filters_summary_rows_and_maps_fields(self):
        payload = {
            "summary": {
                "report_name": "客服数据23年新",
                "file_path": "/home/kk/下载/自定义报表_客服数据23年新_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "melissa",
                    "聊天人数(原咨询人数)": 98.0,
                    "接待人数": 82.0,
                    "直接接入人数": 82.0,
                    "转发接入人数": 0.0,
                    "转出人数": 0.0,
                    "总消息数": 1112.0,
                    "买家消息数": 507.0,
                    "客服消息数": 605.0,
                    "答问比": 1.1933,
                    "客服字数": 26316.0,
                    "最大同时聊天数": 12.0,
                    "未回复人数": 0.0,
                    "回复率": 1.0,
                    "慢接待人数": 0.0,
                    "长接待人数": 10.0,
                    "首次响应(秒)": 27.77,
                    "平均响应(秒)": 37.79,
                    "平均接待时长": "8分48秒",
                },
                {"客服昵称": "汇总", "聊天人数(原咨询人数)": 173.0},
                {"客服昵称": "均值", "聊天人数(原咨询人数)": 14.42},
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("INSERT INTO Xiangwang.customer_service_performance_workload_analysis", sql)
        self.assertIn("('melissa', 98, 82, 82, 0, 0, 1112, 507, 605, 1.1933", sql)
        self.assertIn("'8分48秒'", sql)
        self.assertNotIn("'汇总'", sql)
        self.assertNotIn("'均值'", sql)
        self.assertIn("WHERE `date_time` = '2026-04-20'", sql)

    def test_main_reads_stdin_and_writes_sql(self):
        payload = {
            "summary": {
                "report_name": "客服数据23年新",
                "file_path": "/home/kk/下载/自定义报表_客服数据23年新_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "james",
                    "聊天人数(原咨询人数)": 75.0,
                    "接待人数": 61.0,
                    "直接接入人数": 60.0,
                    "转发接入人数": 1.0,
                    "转出人数": 0.0,
                    "总消息数": 1118.0,
                    "买家消息数": 519.0,
                    "客服消息数": 599.0,
                    "答问比": 1.1541,
                    "客服字数": 25029.0,
                    "最大同时聊天数": 35.0,
                    "未回复人数": 0.0,
                    "回复率": 1.0,
                    "慢接待人数": 0.0,
                    "长接待人数": 11.0,
                    "首次响应(秒)": 28.06,
                    "平均响应(秒)": 36.7,
                    "平均接待时长": "12分3秒",
                }
            ],
        }
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("'james'", stdout.getvalue())
        self.assertIn("'12分3秒'", stdout.getvalue())
        self.assertIn("INSERT INTO Xiangwang.customer_service_performance_workload_analysis", stdout.getvalue())

    def test_build_upsert_sql_deletes_day_when_report_is_empty(self):
        payload = {
            "summary": {
                "report_name": "客服数据23年新",
                "file_path": "/home/kk/下载/自定义报表_客服数据23年新_下单优先判定_2026-04-21至2026-04-21.xlsx",
            },
            "rows": [],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertEqual(
            sql,
            "DELETE FROM Xiangwang.customer_service_performance_workload_analysis\n"
            "WHERE date_time = '2026-04-21';",
        )


if __name__ == "__main__":
    unittest.main()

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_customer_service_data_daily_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_customer_service_data_daily_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareCustomerServiceDataDailySqlTests(unittest.TestCase):
    def test_build_upsert_sql_filters_summary_rows_and_maps_fields(self):
        payload = {
            "summary": {
                "report_name": "人均日接入",
                "file_path": "/home/kk/下载/自定义报表_人均日接入_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "melissa",
                    "接待人数": 82.0,
                    "平均响应(秒)": 37.79,
                    "回复率": 1.0,
                    "询单->最终付款转化率": "延迟统计",
                    "上班天数": 1.0,
                    "服务满意度评价参与率": "延迟统计",
                    "客户满意率": "延迟统计",
                    "服务满意度评价很满意": "延迟统计",
                    "服务满意度评价满意": "延迟统计",
                    "服务满意度评价一般": "延迟统计",
                    "服务满意度评价不满": "延迟统计",
                    "服务满意度评价很不满": "延迟统计",
                },
                {
                    "客服昵称": "汇总",
                    "接待人数": 143.0,
                },
                {
                    "客服昵称": "均值",
                    "接待人数": 11.92,
                },
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("INSERT INTO Xiangwang.customer_service_data_daily", sql)
        self.assertIn("('2026-04-20', 'melissa', 82, 37.79, 1.000, '延迟统计', 1.0", sql)
        self.assertNotIn("'汇总'", sql)
        self.assertNotIn("'均值'", sql)
        self.assertIn("WHERE `日期` = '2026-04-20'", sql)

    def test_build_upsert_sql_fills_blank_with_zero_when_column_has_real_values(self):
        payload = {
            "summary": {
                "report_name": "人均日接入",
                "file_path": "/home/kk/下载/自定义报表_人均日接入_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "zoey",
                    "接待人数": 0,
                    "平均响应(秒)": 0,
                    "回复率": 0,
                    "询单->最终付款转化率": "延迟统计",
                    "上班天数": "",
                    "服务满意度评价参与率": "延迟统计",
                    "客户满意率": "延迟统计",
                    "服务满意度评价很满意": "延迟统计",
                    "服务满意度评价满意": "延迟统计",
                    "服务满意度评价一般": "延迟统计",
                    "服务满意度评价不满": "延迟统计",
                    "服务满意度评价很不满": "延迟统计",
                },
                {
                    "客服昵称": "winnie",
                    "接待人数": 56,
                    "平均响应(秒)": 30.91,
                    "回复率": "100.00%",
                    "询单->最终付款转化率": "延迟统计",
                    "上班天数": 1,
                    "服务满意度评价参与率": "延迟统计",
                    "客户满意率": "延迟统计",
                    "服务满意度评价很满意": "延迟统计",
                    "服务满意度评价满意": "延迟统计",
                    "服务满意度评价一般": "延迟统计",
                    "服务满意度评价不满": "延迟统计",
                    "服务满意度评价很不满": "延迟统计",
                },
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("('2026-04-20', 'zoey', 0, 0.00, 0.000, '延迟统计', 0.0", sql)
        self.assertIn("('2026-04-20', 'winnie', 56, 30.91, 1.000, '延迟统计', 1.0", sql)

    def test_main_reads_stdin_and_writes_sql(self):
        payload = {
            "summary": {
                "report_name": "人均日接入",
                "file_path": "/home/kk/下载/自定义报表_人均日接入_下单优先判定_2026-04-20至2026-04-20.xlsx",
            },
            "rows": [
                {
                    "客服昵称": "james",
                    "接待人数": 61.0,
                    "平均响应(秒)": 36.7,
                    "回复率": 1.0,
                    "询单->最终付款转化率": "",
                    "上班天数": 1.0,
                    "服务满意度评价参与率": "",
                    "客户满意率": "",
                    "服务满意度评价很满意": "",
                    "服务满意度评价满意": "",
                    "服务满意度评价一般": "",
                    "服务满意度评价不满": "",
                    "服务满意度评价很不满": "",
                }
            ],
        }
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("'james'", stdout.getvalue())
        self.assertIn("INSERT INTO Xiangwang.customer_service_data_daily", stdout.getvalue())

    def test_build_upsert_sql_deletes_day_when_report_is_empty(self):
        payload = {
            "summary": {
                "report_name": "人均日接入",
                "file_path": "/home/kk/下载/自定义报表_人均日接入_下单优先判定_2026-04-21至2026-04-21.xlsx",
            },
            "rows": [],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertEqual(
            sql,
            "DELETE FROM Xiangwang.customer_service_data_daily\n"
            "WHERE `日期` = '2026-04-21';",
        )


if __name__ == "__main__":
    unittest.main()

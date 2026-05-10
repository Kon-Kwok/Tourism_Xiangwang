import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_qianniu_shop_data_daily_registration_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_qianniu_shop_data_daily_registration_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareQianniuShopDataDailyRegistrationSqlTests(unittest.TestCase):
    def test_build_upsert_sql_supports_summary_rows_payload(self):
        payload = {
            "summary": {"biz_date": "2026-04-10"},
            "rows": [{"关注店铺人数": 31}],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("INSERT INTO Xiangwang.shop_data_daily_registration", sql)
        self.assertIn("SET `关注店铺人数` = NULL", sql)
        self.assertIn("SET `关注店铺人数` = 31", sql)
        self.assertIn("WHERE NOT EXISTS", sql)
        self.assertNotIn("ON DUPLICATE KEY UPDATE", sql)

    def test_build_upsert_sql_supports_flat_payload(self):
        payload = {
            "biz_date": "2026-04-10",
            "关注店铺人数": 31,
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("SET `关注店铺人数` = 31", sql)

    def test_build_upsert_sql_treats_null_follow_count_as_zero(self):
        payload = {
            "summary": {"biz_date": "2026-04-21"},
            "rows": [{"关注店铺人数": None}],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("SET `关注店铺人数` = 0", sql)

    def test_main_reads_stdin_and_writes_sql(self):
        payload = {
            "summary": {"biz_date": "2026-04-10"},
            "rows": [{"关注店铺人数": 31}],
        }
        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("SET `关注店铺人数` = 31", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

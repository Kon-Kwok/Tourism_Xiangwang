import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_sycm_flow_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_sycm_flow_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareSycmFlowSqlTests(unittest.TestCase):
    def test_build_upsert_sql_updates_existing_daily_key_row_without_duplicate_key(self):
        payload = {
            "summary": {"biz_date": "2026-04-24"},
            "rows": [
                {
                    "访客数": 17884,
                    "浏览量": 35984,
                    "广告流量": 13209,
                    "平台流量": 5788,
                    "关注店铺人数": 26,
                }
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("UPDATE shop_daily_key_data", sql)
        self.assertIn("total_uv = 17884", sql)
        self.assertIn("total_pv = 35984", sql)
        self.assertIn("流量来源广告_uv = 13209", sql)
        self.assertIn("流量来源平台_uv = 5788", sql)
        self.assertIn("SET total_uv = NULL", sql)
        self.assertIn("WHERE NOT EXISTS", sql)
        self.assertNotIn("ON DUPLICATE KEY UPDATE", sql)


if __name__ == "__main__":
    unittest.main()

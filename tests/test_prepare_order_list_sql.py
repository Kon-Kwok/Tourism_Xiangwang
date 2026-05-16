import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_order_list_sql.py"
SPEC = importlib.util.spec_from_file_location("prepare_order_list_sql", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareOrderListSqlTests(unittest.TestCase):
    def test_build_upsert_sql_includes_item_title(self):
        payload = {
            "summary": {"deal_start": "2026-04-16 00:00:00", "order_count": 1, "gmv": 668.98},
            "rows": [
                {
                    "orderId": "4502286399049019434",
                    "item_title": "SC260506 1D3人间升1D4人间 补差 668.98元",
                    "package_type": None,
                    "buy_mount": 1,
                    "actual_fee": "￥668.98",
                    "order_time": "2026-04-16 16:57:54",
                    "status_text": "交易成功",
                }
            ],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("item_title VARCHAR(300)", sql)
        self.assertIn("(order_id, item_title, package_type, buy_mount, actual_fee, order_time, status_text, order_date)", sql)
        self.assertIn("'SC260506 1D3人间升1D4人间 补差 668.98元'", sql)
        self.assertIn("DELETE FROM Xiangwang.order_list WHERE order_date = '2026-04-16'", sql)
        self.assertNotIn("ON DUPLICATE KEY UPDATE", sql)

    def test_build_upsert_sql_clears_existing_day_when_no_rows(self):
        payload = {
            "summary": {"deal_start": "2026-04-17 00:00:00", "order_count": 0, "gmv": 0},
            "rows": [],
        }

        sql = MODULE.build_upsert_sql(payload)

        self.assertIn("CREATE TABLE IF NOT EXISTS Xiangwang.order_list", sql)
        self.assertIn("DELETE FROM Xiangwang.order_list WHERE order_date = '2026-04-17'", sql)
        self.assertIn("-- 没有订单明细需要入库", sql)
        self.assertNotIn("INSERT INTO Xiangwang.order_list", sql)


if __name__ == "__main__":
    unittest.main()

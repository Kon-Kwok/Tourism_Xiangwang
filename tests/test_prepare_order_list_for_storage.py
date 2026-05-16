import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_order_list_for_storage.py"
SPEC = importlib.util.spec_from_file_location("prepare_order_list_for_storage", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareOrderListForStorageTests(unittest.TestCase):
    def test_prepare_payload_for_storage_updates_summary_metrics(self):
        payload = {
            "summary": {"order_count": 3},
            "rows": [
                {
                    "package_type": "阳台3人房通兑",
                    "buy_mount": 1,
                    "actual_fee": "￥10797.00",
                },
                {
                    "package_type": "家庭阳台房3D4人房",
                    "buy_mount": 4,
                    "actual_fee": "￥11554.00",
                },
                {
                    "package_type": "未识别套餐",
                    "buy_mount": 2,
                    "actual_fee": "￥100.50",
                },
            ],
        }

        result = MODULE.prepare_payload_for_storage(payload)

        self.assertEqual(result["summary"]["total_pax"], 9)
        self.assertEqual(result["summary"]["total_booking"], 4)
        self.assertEqual(result["summary"]["gmv"], 22451.5)
        self.assertEqual(result["rows"][0]["buy_mount"], 1)

    def test_prepare_payload_for_storage_counts_amount_only_orders_only_in_gmv(self):
        payload = {
            "summary": {},
            "rows": [
                {
                    "item_title": "SC260506 邮轮双人房",
                    "package_type": "双人阳台房2人房",
                    "buy_mount": 2,
                    "actual_fee": "￥10000.00",
                },
                {
                    "item_title": "SC260506 1D3人间升1D4人间 补差 668.98元",
                    "package_type": None,
                    "buy_mount": 1,
                    "actual_fee": "￥668.98",
                },
                {
                    "item_title": "SC260506 邮轮尾款 2000元",
                    "package_type": "家庭阳台房4人房",
                    "buy_mount": 4,
                    "actual_fee": "￥2000.00",
                },
            ],
        }

        result = MODULE.prepare_payload_for_storage(payload)

        self.assertEqual(result["summary"]["total_pax"], 2)
        self.assertEqual(result["summary"]["total_booking"], 1)
        self.assertEqual(result["summary"]["gmv"], 12668.98)

    def test_prepare_payload_for_storage_recognizes_chinese_room_capacity_prefix(self):
        payload = {
            "summary": {},
            "rows": [
                {
                    "package_type": "双人内舱房4V",
                    "buy_mount": 2,
                    "actual_fee": "￥5834.00",
                },
                {
                    "package_type": "三人间",
                    "buy_mount": 3,
                    "actual_fee": "￥9000.00",
                },
            ],
        }

        result = MODULE.prepare_payload_for_storage(payload)

        self.assertEqual(result["summary"]["total_pax"], 5)
        self.assertEqual(result["summary"]["total_booking"], 2)
        self.assertEqual(result["summary"]["gmv"], 14834)

    def test_main_reads_stdin_and_writes_json(self):
        payload = {
            "summary": {},
            "rows": [
                {
                    "package_type": "阳台2人房通兑",
                    "buy_mount": 2,
                    "actual_fee": "￥9998.00",
                }
            ],
        }

        stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        stdout = io.StringIO()

        with mock.patch("sys.stdin", stdin), mock.patch("sys.stdout", stdout):
            exit_code = MODULE.main()

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["summary"]["total_pax"], 4)
        self.assertEqual(result["summary"]["total_booking"], 2)
        self.assertEqual(result["summary"]["gmv"], 9998)


if __name__ == "__main__":
    unittest.main()

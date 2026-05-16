import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "bin" / "prepare_shop_kpi_api_to_json.py"
SPEC = importlib.util.spec_from_file_location("prepare_shop_kpi_api_to_json", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class PrepareShopKpiApiToJsonTests(unittest.TestCase):
    def test_build_payload_maps_daily_report_and_delay_fields(self):
        payload = MODULE.build_payload(
            {
                "valueList": [
                    {
                        "show_name": "zoey",
                        "service_buyer_num": 0,
                        "avg_total_reply_cost": 0,
                        "reply_percent": 0,
                        "ask_today_final_paid_succrate": None,
                        "work_days": None,
                        "new_eval_receive_rate": None,
                        "new_customer_satisfied_rate": None,
                        "new_very_satisfied_num": None,
                        "new_satisfied_num": None,
                        "new_general_num": None,
                        "new_dissatisfied_num": None,
                        "new_very_dissatisfied_num": None,
                        "delay_fields": [
                            "ask_today_final_paid_succrate",
                            "new_eval_receive_rate",
                            "new_customer_satisfied_rate",
                            "new_very_satisfied_num",
                            "new_satisfied_num",
                            "new_general_num",
                            "new_dissatisfied_num",
                            "new_very_dissatisfied_num",
                        ],
                    }
                ],
                "fields": ["service_buyer_num"],
            },
            "人均日接入",
            "2026-05-15",
        )

        self.assertEqual(payload["summary"]["source"], "topchitu_api")
        self.assertEqual(payload["summary"]["report_name"], "人均日接入")
        self.assertEqual(payload["rows"][0]["客服昵称"], "zoey")
        self.assertEqual(payload["rows"][0]["上班天数"], "")
        self.assertEqual(payload["rows"][0]["询单->最终付款转化率"], "延迟统计")
        self.assertEqual(payload["rows"][0]["客户满意率"], "延迟统计")

    def test_build_payload_maps_summary_report(self):
        payload = MODULE.build_payload(
            {
                "valueList": [
                    {
                        "show_name": "winnie",
                        "all_chat_buyer_num": 56,
                        "service_buyer_num": 56,
                        "ask_num": None,
                        "employee_payments_with_deduct": 123.45,
                        "employee_item_num_with_deduct": 2,
                        "employee_paid_num": 1,
                        "employee_trade_num": 1,
                        "delay_fields": ["ask_num"],
                    }
                ]
            },
            "每周店铺个人数据",
            "2026-05-15",
        )

        self.assertEqual(payload["rows"][0]["客服昵称"], "winnie")
        self.assertEqual(payload["rows"][0]["聊天人数(原咨询人数)"], 56)
        self.assertEqual(payload["rows"][0]["询单人数"], "延迟统计")
        self.assertEqual(payload["rows"][0]["销售额"], 123.45)

    def test_build_payload_maps_workload_report(self):
        payload = MODULE.build_payload(
            {
                "valueList": [
                    {
                        "show_name": "liz",
                        "all_chat_buyer_num": 50,
                        "service_buyer_num": 50,
                        "service_direct_buyer_num": 49,
                        "service_in_buyer_num": 1,
                        "service_out_buyer_num": 0,
                        "total_message_num": 100,
                        "buyer_message_num": 40,
                        "seller_message_num": 60,
                        "seller_buyer_message_percent": 1.5,
                        "waitor_word_num": 2000,
                        "max_concurrent_reception_buyer_num": 5,
                        "no_reply_chatpeer_num": 0,
                        "reply_percent": 1,
                        "slow_reception_chatpeer_num": 0,
                        "long_receive_chatpeer_num": 1,
                        "avg_first_reply_cost": 10.1,
                        "avg_total_reply_cost": 20.2,
                        "extra_avg_total_reception_cost_chart": 300,
                    }
                ]
            },
            "客服数据23年新",
            "2026-05-15",
        )

        row = payload["rows"][0]
        self.assertEqual(row["客服昵称"], "liz")
        self.assertEqual(row["转发接入人数"], 1)
        self.assertEqual(row["答问比"], 1.5)
        self.assertEqual(row["平均接待时长"], 300)


if __name__ == "__main__":
    unittest.main()

import unittest
from decimal import Decimal
from unittest import mock

from tourism_automation.collectors.alimama_daily.client import AlimamaDailyClient, OneAlimamaTokens
from tourism_automation.collectors.alimama_daily.excel_rules import SHEET_FIELDS, calculate_excel_metrics
from tourism_automation.collectors.alimama_daily.normalize import normalize_alimama_daily_payloads
from tourism_automation.collectors.alimama_daily.storage import AlimamaDailyStorage


class AlimamaDailyClientTests(unittest.TestCase):
    def test_fetch_onebp_scene_report_posts_stable_payload(self):
        http = mock.Mock()
        http.session.post.return_value.status_code = 200
        http.session.post.return_value.json.return_value = {"data": {"list": []}, "info": {"ok": True}}
        http.session.post.return_value.raise_for_status.return_value = None
        client = AlimamaDailyClient(
            http=http,
            tokens=OneAlimamaTokens(csrf_id="csrf_1_1_1", login_point_id="login123"),
        )

        client.fetch_onebp_scene_report(biz_date="2026-05-01")

        call = http.session.post.call_args
        self.assertEqual(call.kwargs["params"]["csrfId"], "csrf_1_1_1")
        payload = call.kwargs["json"]
        self.assertEqual(payload["startTime"], "2026-05-01")
        self.assertEqual(payload["endTime"], "2026-05-01")
        self.assertEqual(payload["effectEqual"], 3)
        self.assertEqual(payload["queryDomains"], ["scene"])
        self.assertIn("adPv", payload["queryFieldIn"])


class AlimamaDailyNormalizeTests(unittest.TestCase):
    def test_tmall_express_fields_match_excel_order_without_cpm(self):
        self.assertEqual(
            SHEET_FIELDS["tmall_express"],
            [
                "cost",
                "imp",
                "click",
                "order_count",
                "sales",
                "shopping_cart",
                "bookmark_product",
                "bookmark_store",
                "ctr",
                "cpc",
                "roi",
                "cvr",
                "asp",
                "cporder",
                "cpshopping_cart",
                "collection_cart_cost",
                "collection_cart_count",
                "collection_cart_rate",
            ],
        )
        self.assertNotIn("cpm", SHEET_FIELDS["tmall_express"])

    def test_cpm_is_sheet_specific_not_applied_to_tmall_express(self):
        row = {
            "cost": 200,
            "imp": 1000,
            "click": 50,
            "order_count": 2,
            "sales": 1000,
            "shopping_cart": 3,
            "bookmark_product": 1,
            "bookmark_store": 0,
        }

        tmall = calculate_excel_metrics(row, date_time="2026-05-01", sheet="tmall_express")
        wanxiangtai = calculate_excel_metrics(row, date_time="2026-05-01", sheet="wanxiangtai")
        gravity = calculate_excel_metrics(
            row,
            date_time="2026-05-01",
            sheet="gravity_rubiks_cube",
            previous_row={**row, "cost": 1, "imp": 1},
        )

        self.assertNotIn("cpm", tmall)
        self.assertEqual(wanxiangtai["cpm"], Decimal("200.00"))
        self.assertEqual(gravity["cpm"], Decimal("200.00"))

    def test_advertising_formula_fields_match_daily_rules(self):
        row = {
            "cost": 100,
            "imp": 1000,
            "click": 50,
            "order_count": 2,
            "sales": 400,
            "shopping_cart": 3,
            "bookmark_product": 2,
            "bookmark_store": 0,
        }

        metrics = calculate_excel_metrics(row, date_time="2026-05-01", sheet="wanxiangtai")

        self.assertEqual(metrics["ctr"], Decimal("0.050000"))
        self.assertEqual(metrics["cpc"], Decimal("2.00"))
        self.assertEqual(metrics["cpm"], Decimal("100.00"))
        self.assertEqual(metrics["roi"], Decimal("4.0000"))
        self.assertEqual(metrics["cvr"], Decimal("0.040000"))
        self.assertEqual(metrics["collection_cart_count"], Decimal("5"))
        self.assertEqual(metrics["collection_cart_cost"], Decimal("20.00"))
        self.assertEqual(metrics["collection_cart_rate"], Decimal("0.100000"))

    def test_normalize_alimama_daily_payloads_maps_channels_and_totals_wanxiangtai(self):
        star_store_payload = {
            "data": {
                "rptQueryResp": {
                    "rptDataSum": [
                        {
                            "impression": 512,
                            "cost": 88492,
                            "click": 126,
                            "transactionshippingtotal": 0,
                            "transactiontotal": 0,
                            "carttotal": 9,
                            "favitemtotal": 1,
                            "favshoptotal": 4,
                        }
                    ]
                }
            }
        }
        scene_payload = {
            "data": {
                "list": [
                    {
                        "scene1Name": "人群推广",
                        "charge": 1477.64,
                        "adPv": 50113,
                        "click": 1719,
                        "alipayInshopNum": 1,
                        "alipayInshopAmt": 17548.02,
                        "cartInshopNum": 13,
                        "itemColInshopNum": 24,
                        "shopColDirNum": 1,
                    },
                    {
                        "scene1Name": "关键词推广",
                        "charge": 1328.25,
                        "adPv": 12559,
                        "click": 568,
                        "cartInshopNum": 14,
                        "itemColInshopNum": 3,
                        "shopColDirNum": 0,
                    },
                    {
                        "scene1Name": "超级短视频",
                        "charge": 890.37,
                        "adPv": 10420,
                        "click": 433,
                        "cartInshopNum": 3,
                        "itemColInshopNum": 2,
                        "shopColDirNum": 0,
                    },
                    {"scene1Name": "超级直播", "charge": 0, "adPv": 3, "click": 0},
                ]
            }
        }

        result = normalize_alimama_daily_payloads(
            biz_date="2026-05-01",
            star_store_payload=star_store_payload,
            scene_payload=scene_payload,
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["channels"]["tmall_express"]["imp"], 12559)
        self.assertEqual(result["channels"]["gravity_rubiks_cube"]["order_count"], 1)
        self.assertEqual(result["channels"]["wanxiangtai"]["imp"], 10423)
        self.assertEqual(result["channels"]["wanxiangtai"]["bookmark_product"], 2)
        self.assertEqual(result["channels"]["wanxiangtai"]["bookmark_store"], 0)
        self.assertEqual(result["wanxiangtai_2_rows"]["超级短视频"]["data_source"], "超级短视频")
        self.assertEqual(result["wanxiangtai_2_rows"]["小计"]["data_source"], "小计")
        self.assertEqual(result["wanxiangtai_2_rows"]["小计"]["bookmark_store"], 0)
        self.assertEqual(result["wanxiangtai_2_rows"]["小计"]["collection_cart_count"], Decimal("5"))
        self.assertEqual(result["channels"]["star_store"]["cost"], Decimal("884.92"))


class AlimamaDailyStorageTests(unittest.TestCase):
    def test_save_rejects_partial_result_with_clear_missing_channels(self):
        storage = AlimamaDailyStorage(config={})
        result = {
            "date_time": "2026-05-15",
            "channels": {"wanxiangtai": {}},
            "wanxiangtai_2_rows": {},
        }

        with self.assertRaisesRegex(RuntimeError, "star_store, tmall_express, gravity_rubiks_cube"):
            storage.save(result)

    @mock.patch.object(AlimamaDailyStorage, "_connect")
    def test_save_formats_percent_and_currency_fields_as_text(self, mock_connect):
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        metrics = {
            "cost": Decimal("12.34"),
            "imp": 1000,
            "click": 50,
            "order_count": 2,
            "sales": Decimal("200.00"),
            "shopping_cart": 3,
            "bookmark_product": 2,
            "bookmark_store": 1,
            "ctr": Decimal("0.05"),
            "cpc": Decimal("0.25"),
            "cpm": Decimal("12.34"),
            "roi": Decimal("16.2000"),
            "cvr": Decimal("0.04"),
            "asp": Decimal("100.00"),
            "cporder": Decimal("6.17"),
            "cpshopping_cart": Decimal("4.11"),
            "cart_rate": Decimal("0.06"),
            "collection_cart_cost": Decimal("4.11"),
            "collection_cart_count": 5,
            "collection_cart_rate": Decimal("0.10"),
        }
        result = {
            "date_time": "2026-05-15",
            "channels": {
                "star_store": metrics,
                "tmall_express": metrics,
                "gravity_rubiks_cube": metrics,
                "wanxiangtai": metrics,
            },
            "wanxiangtai_2_rows": {
                "超级短视频": {**metrics, "data_source": "超级短视频"},
                "小计": {**metrics, "data_source": "小计"},
            },
        }

        storage = AlimamaDailyStorage(config={})
        storage.save(result)

        star_insert = next(call for call in mock_cursor.execute.call_args_list if "INSERT INTO star_store" in call.args[0])
        tmall_insert = next(call for call in mock_cursor.execute.call_args_list if "INSERT INTO tmall_express" in call.args[0])
        wanxiangtai_2_insert = next(call for call in mock_cursor.execute.call_args_list if "INSERT INTO wanxiangtai_2" in call.args[0])

        self.assertIn("￥12.34", star_insert.args[1])
        self.assertIn("￥200.00", star_insert.args[1])
        self.assertIn("￥0.25", star_insert.args[1])
        self.assertIn("5.00%", star_insert.args[1])
        self.assertIn("6.00%", star_insert.args[1])

        self.assertIn("￥4.11", tmall_insert.args[1])
        self.assertIn("10.00%", tmall_insert.args[1])
        self.assertIn("￥4.11", wanxiangtai_2_insert.args[1])
        self.assertIn("10.00%", wanxiangtai_2_insert.args[1])


if __name__ == "__main__":
    unittest.main()

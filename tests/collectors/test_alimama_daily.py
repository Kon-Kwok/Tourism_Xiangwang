import unittest
from decimal import Decimal
from unittest import mock

from tourism_automation.collectors.alimama_daily.client import AlimamaDailyClient, OneAlimamaTokens
from tourism_automation.collectors.alimama_daily.normalize import normalize_alimama_daily_payloads


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


if __name__ == "__main__":
    unittest.main()

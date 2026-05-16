import unittest
from decimal import Decimal
from unittest import mock

from tourism_automation.collectors.fliggy_star_store.client import FliggyStarStoreClient
from tourism_automation.collectors.fliggy_star_store.normalize import normalize_star_store_payload
from tourism_automation.collectors.fliggy_star_store.storage import FliggyStarStoreStorage


class FliggyStarStoreClientTests(unittest.TestCase):
    def test_fetch_report_uses_stable_http_parameters(self):
        http = mock.Mock()
        http.session.get.return_value.status_code = 200
        http.session.get.return_value.headers = {"content-type": "application/json"}
        http.session.get.return_value.text = '{"data":{"rptQueryResp":{"rptDataSum":[]}}}'
        http.session.get.return_value.json.return_value = {"data": {"rptQueryResp": {"rptDataSum": []}}}

        client = FliggyStarStoreClient(http=http)
        client.fetch_report(biz_date="2026-05-08")

        http.session.get.assert_called_once()
        call = http.session.get.call_args
        self.assertEqual(call.kwargs["params"]["startdate"], "2026-05-08")
        self.assertEqual(call.kwargs["params"]["enddate"], "2026-05-08")
        self.assertEqual(call.kwargs["params"]["productid"], "101005202")
        self.assertEqual(call.kwargs["params"]["effect"], "3")
        self.assertEqual(call.kwargs["params"]["type"], "click")
        self.assertEqual(call.kwargs["params"]["offset"], 0)
        self.assertEqual(call.kwargs["params"]["pagesize"], 20)
        self.assertNotIn("csrfID", call.kwargs["params"])

    def test_fetch_report_rejects_login_html(self):
        http = mock.Mock()
        http.session.get.return_value.status_code = 200
        http.session.get.return_value.headers = {"content-type": "text/html"}
        http.session.get.return_value.text = "<!doctype html><title>登录</title>"

        client = FliggyStarStoreClient(http=http)

        with self.assertRaisesRegex(RuntimeError, "authentication"):
            client.fetch_report(biz_date="2026-05-08")


class FliggyStarStoreNormalizeTests(unittest.TestCase):
    def test_normalize_star_store_payload_maps_and_calculates_metrics(self):
        payload = {
            "data": {
                "rptQueryResp": {
                    "rptDataSum": [
                        {
                            "thedate": "2026-05-08",
                            "impression": 671,
                            "cost": 118015.0,
                            "click": 159,
                            "transactionshippingtotal": 3,
                            "transactiontotal": 2795000.0,
                            "carttotal": 25,
                            "favitemtotal": 3,
                            "favshoptotal": 2,
                        }
                    ]
                }
            }
        }

        result = normalize_star_store_payload(payload, biz_date="2026-05-08")
        metrics = result["metrics"]

        self.assertEqual(result["status"], "success")
        self.assertEqual(metrics["date_time"], "2026-05-08")
        self.assertEqual(str(metrics["cost"]), "1180.15")
        self.assertEqual(metrics["imp"], 671)
        self.assertEqual(metrics["click"], 159)
        self.assertEqual(metrics["order_count"], 3)
        self.assertEqual(str(metrics["sales"]), "27950.00")
        self.assertEqual(metrics["shopping_cart"], 25)
        self.assertEqual(metrics["bookmark_product"], 3)
        self.assertEqual(metrics["bookmark_store"], 2)
        self.assertEqual(str(metrics["ctr"]), "0.236960")
        self.assertEqual(str(metrics["cpc"]), "7.42")
        self.assertEqual(str(metrics["cpm"]), "1758.79")
        self.assertEqual(str(metrics["roi"]), "23.6834")
        self.assertEqual(str(metrics["cvr"]), "0.018868")
        self.assertEqual(str(metrics["asp"]), "9316.67")
        self.assertEqual(str(metrics["cporder"]), "393.38")
        self.assertEqual(str(metrics["cpshopping_cart"]), "47.21")
        self.assertEqual(str(metrics["cart_rate"]), "0.157233")

    def test_normalize_star_store_payload_returns_no_data_without_rows(self):
        payload = {"data": {"rptQueryResp": {"rptDataSum": []}}}

        result = normalize_star_store_payload(payload, biz_date="2026-05-09")

        self.assertEqual(result["status"], "no_data")
        self.assertEqual(result["date_time"], "2026-05-09")
        self.assertIsNone(result["metrics"])

    def test_normalize_star_store_payload_returns_no_data_for_date_only_row(self):
        payload = {"data": {"rptQueryResp": {"rptDataDaily": [{"thedate": "2026-05-09"}], "rptDataSum": []}}}

        result = normalize_star_store_payload(payload, biz_date="2026-05-09")

        self.assertEqual(result["status"], "no_data")
        self.assertIsNone(result["metrics"])


class FliggyStarStoreStorageTests(unittest.TestCase):
    @mock.patch.object(FliggyStarStoreStorage, "_connect")
    def test_save_formats_money_and_percentage_fields_as_text(self, mock_connect):
        mock_conn = mock.MagicMock()
        mock_cursor = mock.MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        storage = FliggyStarStoreStorage(config={})
        result = {
            "status": "success",
            "metrics": {
                "date_time": "2026-05-08",
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
            },
        }

        storage.save(result)

        insert_call = next(call for call in mock_cursor.execute.call_args_list if "INSERT INTO star_store" in call.args[0])
        params = insert_call.args[1]
        self.assertIn("￥12.34", params)
        self.assertIn("￥200.00", params)
        self.assertIn("￥0.25", params)
        self.assertIn("5.00%", params)
        self.assertIn("6.00%", params)

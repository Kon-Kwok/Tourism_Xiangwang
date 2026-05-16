import io
import json
import unittest
from contextlib import redirect_stdout
from unittest import mock

from tourism_automation.collectors.sycm import cli as sycm_cli
from tourism_automation.collectors.sycm.collector import HomePageCollector
from tourism_automation.collectors.sycm.normalize import normalize_home_payloads
from tourism_automation.collectors.sycm.universal_client import PageDataResult
from tourism_automation.shared.chrome.session import _decrypt_cookie_value, build_chrome_session


class NormalizeHomePayloadsTests(unittest.TestCase):
    def test_normalize_home_payloads_emits_metrics_and_trends(self):
        overview_payload = {
            "content": {
                "code": 0,
                "data": {
                    "self": {
                        "statDate": {"value": 1776528000000},
                        "payAmt": {
                            "value": 40552.99,
                            "cycleCrc": -0.8390799257,
                            "syncCrc": 0.0985501562,
                            "yearSyncCrc": 0.9212142316,
                        },
                        "uv": {
                            "value": 10749,
                            "cycleCrc": -0.3620014245,
                            "syncCrc": -0.5784705882,
                            "yearSyncCrc": -0.1271619976,
                        },
                    }
                },
            },
            "hasError": False,
        }
        trend_payload = {
            "content": {
                "code": 0,
                "data": {
                    "self": {
                        "statDate": [1776441600000, 1776528000000],
                        "payAmt": [252007.03, 40552.99],
                        "uv": [16848, 10749],
                    },
                    "rivalAvg": {
                        "statDate": [1776441600000, 1776528000000],
                        "payAmt": [77187.2, 78490.4],
                        "uv": [3621, 3438],
                    },
                    "rivalGood": {
                        "statDate": [1776441600000, 1776528000000],
                        "payAmt": [198404, 197284.9],
                        "uv": [10063, 8381],
                    },
                },
            },
            "hasError": False,
        }
        table_payload = {
            "content": {
                "code": 0,
                "data": [
                    {
                        "statDate": {"value": 1776528000000},
                        "payAmt": {"value": 40552.99},
                        "uv": {"value": 10749},
                    }
                ],
            },
            "hasError": False,
        }

        normalized = normalize_home_payloads(
            biz_date="2026-04-19",
            shop_name="皇家加勒比国际游轮旗舰店",
            overview_payload=overview_payload,
            trend_payload=trend_payload,
            table_payload=table_payload,
        )

        self.assertEqual(normalized["metrics"][0]["metric_code"], "payAmt")
        self.assertEqual(normalized["metrics"][0]["metric_value"], 40552.99)
        self.assertEqual(normalized["metrics"][1]["metric_code"], "uv")
        self.assertEqual(normalized["table_rows"][0]["stat_date"], "2026-04-19")
        self.assertEqual(normalized["trends"][0]["stat_date"], "2026-04-18")
        self.assertEqual(normalized["trends"][0]["rival_good_value"], 198404.0)


class HomePageCollectorTests(unittest.TestCase):
    @mock.patch("tourism_automation.collectors.sycm.collector.UniversalSycmClient", create=True)
    @mock.patch("tourism_automation.collectors.sycm.collector.SycmHomeClient")
    def test_collect_uses_flow_monitor_when_today_homepage_row_is_placeholder(
        self,
        mock_home_client_cls,
        mock_universal_client_cls,
    ):
        overview_payload = {
            "content": {
                "code": 0,
                "data": {
                    "self": {},
                    "supportQueryByLy": False,
                },
            },
            "hasError": False,
        }
        trend_payload = {
            "content": {
                "code": 0,
                "data": {
                    "self": {
                        "statDate": [1776614400000, 1776700800000],
                        "payAmt": [69298.0, 0.0],
                        "uv": [13662, 0],
                    },
                },
            },
            "hasError": False,
        }
        table_payload = {
            "content": {
                "code": 0,
                "data": [
                    {
                        "statDate": {"value": 1776614400000},
                        "payAmt": {"value": 69298.0, "cycleCrc": 0.708825909},
                        "uv": {"value": 13662, "cycleCrc": 0.2710019537},
                    },
                    {
                        "statDate": {"value": 1776700800000},
                        "payAmt": {"value": 0.0, "cycleCrc": -1.0},
                        "uv": {"value": 0, "cycleCrc": -1.0},
                    },
                ],
            },
            "hasError": False,
        }

        mock_home_client = mock.Mock()
        mock_home_client.fetch_home_payloads.return_value = (
            overview_payload,
            trend_payload,
            table_payload,
        )
        mock_home_client_cls.return_value = mock_home_client

        mock_universal_client = mock.Mock()
        mock_universal_client.fetch_page_endpoint.return_value = PageDataResult(
            page_id="flow_monitor",
            page_name="流量监控",
            endpoint_name="overview",
            status="success",
            data={
                "code": 0,
                "data": {
                    "payAmt": {"value": 69298.0},
                    "uv": {"value": 13653},
                },
            },
        )
        mock_universal_client_cls.return_value = mock_universal_client

        payload = HomePageCollector(http=mock.sentinel.http).collect(
            biz_date="2026-04-21",
            shop_name="SYCM",
        )

        self.assertTrue(payload["metrics"])
        self.assertEqual(payload["metrics"][0]["metric_code"], "payAmt")
        self.assertEqual(payload["metrics"][0]["metric_value"], 69298.0)
        self.assertEqual(payload["table_rows"][-1]["stat_date"], "2026-04-21")
        self.assertEqual(payload["table_rows"][-1]["payAmt"], 69298.0)
        self.assertEqual(payload["table_rows"][-1]["uv"], 13653.0)
        self.assertEqual(payload["trends"][-1]["stat_date"], "2026-04-21")
        self.assertEqual(payload["trends"][-1]["self_value"], 13653.0)
        mock_universal_client.fetch_page_endpoint.assert_called_once_with(
            page_id="flow_monitor",
            endpoint_name="overview",
            date_range="2026-04-20|2026-04-21,2026-04-21|2026-04-21",
            device="2",
        )


class SycmCliTests(unittest.TestCase):
    @mock.patch("tourism_automation.collectors.sycm.cli._today_local_str", return_value="2026-04-21", create=True)
    @mock.patch("tourism_automation.collectors.sycm.cli.ShopSourceCollector")
    @mock.patch("tourism_automation.collectors.sycm.cli.ChromeHttpClient")
    def test_flow_monitor_outputs_summary_and_rows_structure(
        self,
        mock_http_cls,
        mock_shop_source_cls,
        _mock_today,
    ):
        mock_http = mock.Mock()
        mock_http.fetch_json.return_value = {
            "code": 0,
            "data": {
                "uv": {"value": 14057},
                "pv": {"value": 27236},
                "shopCltByrCnt": {"value": 24},
                "payAmt": {"value": 69298.0},
            },
        }
        mock_http_cls.from_local_chrome.return_value = mock_http
        mock_shop_source = mock.Mock()
        mock_shop_source.collect.return_value = {
            "metrics": [
                {"source_name": "广告流量", "uv": 10510},
                {"source_name": "平台流量", "uv": 4030},
            ]
        }
        mock_shop_source_cls.return_value = mock_shop_source

        args = mock.Mock(
            collector_command="flow-monitor",
            date="2026-04-21",
            shop_name="SYCM",
            device="2",
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = sycm_cli.run(args)

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(
            payload,
            {
                "summary": {
                    "source": "chrome_cookie_http",
                    "shop_name": "SYCM",
                    "page_code": "flow_monitor",
                    "page_name": "流量监控概览",
                    "biz_date": "2026-04-21",
                    "device": "2",
                    "row_count": 1,
                },
                "rows": [
                    {
                        "访客数": 14057,
                        "浏览量": 27236,
                        "关注店铺人数": 24,
                        "广告流量": 10510,
                        "平台流量": 4030,
                    }
                ],
            },
        )
        mock_http.fetch_json.assert_called_once_with(
            "https://sycm.taobao.com/flow/new/live/guide/trend/overview.json"
            "?dateType=today&dateRange=2026-04-21%7C2026-04-21&device=0",
            referer="https://sycm.taobao.com/flow/monitor/overview?dateRange=2026-04-21%7C2026-04-21&dateType=today",
        )
        mock_shop_source.collect.assert_called_once_with(
            biz_date="2026-04-21",
            shop_name="SYCM",
        )

    @mock.patch("tourism_automation.collectors.sycm.cli._today_local_str", return_value="2026-04-21", create=True)
    @mock.patch("tourism_automation.collectors.sycm.cli.ShopSourceCollector")
    @mock.patch("tourism_automation.collectors.sycm.cli.ChromeHttpClient")
    def test_flow_monitor_uses_historical_endpoint_for_non_today_dates(
        self,
        mock_http_cls,
        mock_shop_source_cls,
        _mock_today,
    ):
        mock_http = mock.Mock()
        mock_http.fetch_json.return_value = {
            "code": 0,
            "data": {
                "uv": {"value": 13653},
                "pv": {"value": 31835},
                "shopCltByrCnt": {"value": 26},
            },
        }
        mock_http_cls.from_local_chrome.return_value = mock_http
        mock_shop_source = mock.Mock()
        mock_shop_source.collect.return_value = {"metrics": []}
        mock_shop_source_cls.return_value = mock_shop_source

        args = mock.Mock(
            collector_command="flow-monitor",
            date="2026-04-20",
            shop_name="SYCM",
            device="2",
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = sycm_cli.run(args)

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["summary"]["row_count"], 1)
        self.assertEqual(payload["rows"][0]["访客数"], 13653)
        self.assertEqual(payload["rows"][0]["浏览量"], 31835)
        self.assertEqual(payload["rows"][0]["关注店铺人数"], 26)
        mock_http.fetch_json.assert_called_once_with(
            "https://sycm.taobao.com/flow/long/period/nodistinct/new/guide/trend/overview.json"
            "?dateType=compareRange&dateRange=2026-04-20%7C2026-04-20%2C2026-04-19%7C2026-04-19"
            "&indexCode=uv%2CitmUv%2CpayByrCnt&device=2",
            referer="https://sycm.taobao.com/flow/monitor/overview?dateRange=2026-04-20%7C2026-04-20%2C2026-04-19%7C2026-04-19&dateType=compareRange",
        )

    @mock.patch("tourism_automation.collectors.sycm.cli.ShopSourceStorage")
    @mock.patch("tourism_automation.collectors.sycm.cli.ShopSourceCollector")
    @mock.patch("tourism_automation.collectors.sycm.cli.ChromeHttpClient")
    def test_shop_source_collect_save_writes_to_xiangwang(
        self,
        mock_http_cls,
        mock_shop_source_cls,
        mock_storage_cls,
    ):
        mock_http_cls.from_local_chrome.return_value = mock.Mock()
        mock_shop_source_cls.return_value.collect.return_value = {
            "summary": {"collection_date": "2026-04-20", "shop_name": "SYCM"},
            "metrics": [{"source_name": "广告流量", "uv": 10510}],
        }
        mock_storage_cls.return_value.save.return_value = 12

        args = mock.Mock(
            collector_command="shop-source",
            shop_source_command="collect",
            date="2026-04-20",
            shop_name="SYCM",
            active_key="item",
            belong="all",
            device="2",
            save=True,
        )

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = sycm_cli.run(args)

        self.assertEqual(exit_code, 0)
        mock_storage_cls.assert_called_once_with(
            config={"host": "localhost", "user": "root", "database": "Xiangwang"}
        )
        mock_storage_cls.return_value.ensure_schema.assert_called_once_with()
        mock_storage_cls.return_value.save.assert_called_once()
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["saved"])
        self.assertEqual(payload["batch_id"], 12)



class ChromeCookieDecryptTests(unittest.TestCase):
    def test_decrypt_cookie_value_returns_plain_bytes_when_not_encrypted(self):
        result = _decrypt_cookie_value(
            encrypted_value=b"plain-cookie",
            key=b"0" * 16,
            host_hash_len=32,
        )

        self.assertEqual(result, "plain-cookie")

    @mock.patch("tourism_automation.shared.chrome.session._read_chrome_safe_storage_secret", return_value="secret")
    @mock.patch("tourism_automation.shared.chrome.session._read_cookie_db_version", return_value=24)
    @mock.patch("tourism_automation.shared.chrome.session.sqlite3.connect")
    def test_build_chrome_session_loads_fliggy_and_taobao_domains(
        self,
        mock_connect,
        _mock_version,
        _mock_secret,
    ):
        rows = [
            (".taobao.com", "_tb_token_", "token-value", b"", "/"),
            ("sell.fliggy.com", "cookie2", "cookie2-value", b"", "/"),
            ("fsc.fliggy.com", "JSESSIONID", "jsession", b"", "/"),
        ]
        mock_cursor = mock.Mock()
        mock_cursor.fetchall.return_value = rows
        mock_conn = mock.Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        session = build_chrome_session()

        self.assertEqual(session.cookies.get("_tb_token_"), "token-value")
        self.assertEqual(session.cookies.get("cookie2"), "cookie2-value")
        self.assertEqual(session.cookies.get("JSESSIONID"), "jsession")
        executed_sql = mock_cursor.execute.call_args[0][0]
        self.assertIn("sell.fliggy.com", executed_sql)
        self.assertIn("fsc.fliggy.com", executed_sql)


if __name__ == "__main__":
    unittest.main()

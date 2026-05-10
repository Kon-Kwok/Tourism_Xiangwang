import unittest
from unittest import mock
from datetime import datetime
import io
import json

from tourism_automation.cli.main import build_parser


class UnifiedCliTests(unittest.TestCase):
    def test_build_parser_registers_collectors(self):
        parser = build_parser()
        collector_action = next(action for action in parser._actions if action.dest == "collector")

        self.assertEqual(
            sorted(collector_action.choices.keys()),
            [
                "alimama-daily",
                "fliggy-home",
                "fliggy-kpi",
                "fliggy-order-list",
                "fliggy-star-store",
                "shop-kpi-export",
                "shop-kpi-export-batch",
                "sycm",
            ],
        )

    @mock.patch("tourism_automation.collectors.alimama_daily.cli.AlimamaDailyStorage")
    @mock.patch("tourism_automation.collectors.alimama_daily.cli.collect_alimama_daily")
    def test_alimama_daily_collect_accepts_save(self, mock_collect, mock_storage_cls):
        parser = build_parser()
        mock_collect.return_value = {
            "status": "success",
            "date_time": "2026-05-01",
            "channels": {
                "star_store": {"cost": 1, "imp": 2, "click": 3, "order_count": 4},
                "tmall_express": {"cost": 5, "imp": 6, "click": 7, "order_count": 8},
                "gravity_rubiks_cube": {"cost": 9, "imp": 10, "click": 11, "order_count": 12},
                "wanxiangtai": {"cost": 13, "imp": 14, "click": 15, "order_count": 16},
            },
            "wanxiangtai_2_rows": {"小计": {}},
            "missing_channels": [],
        }
        mock_storage_cls.return_value.save.return_value = {"tmall_express": True}

        args = parser.parse_args(
            [
                "alimama-daily",
                "collect",
                "--date",
                "2026-05-01",
                "--save",
                "--mysql-password",
                "pw",
                "--omit-raw",
            ]
        )
        with mock.patch("sys.stdout", new_callable=io.StringIO):
            exit_code = args.handler(args)

        self.assertEqual(exit_code, 0)
        mock_collect.assert_called_once_with(biz_date="2026-05-01")
        mock_storage_cls.return_value.save.assert_called_once_with(mock_collect.return_value)

    @mock.patch("tourism_automation.collectors.alimama_daily.cli.collect_alimama_daily")
    def test_alimama_daily_collect_json_outputs_payload(self, mock_collect):
        parser = build_parser()
        mock_collect.return_value = {
            "status": "success",
            "date_time": "2026-05-01",
            "channels": {},
            "wanxiangtai_2_rows": {},
            "missing_channels": [],
        }

        args = parser.parse_args(["alimama-daily", "collect", "--date", "2026-05-01", "--json", "--omit-raw"])
        with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = args.handler(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["date_time"], "2026-05-01")

    def test_order_list_list_uses_defaults(self):
        parser = build_parser()

        args = parser.parse_args(["fliggy-order-list", "list"])

        self.assertEqual(args.page_num, 1)
        self.assertEqual(args.page_size, 10)

    @mock.patch("tourism_automation.collectors.fliggy_order_list.cli.collect_order_list")
    @mock.patch("tourism_automation.collectors.fliggy_order_list.cli._now_local")
    def test_order_list_list_uses_yesterday_deal_range_defaults(self, mock_now, mock_collect):
        parser = build_parser()
        mock_now.return_value = datetime(2026, 4, 21, 8, 0, 0)
        mock_collect.return_value = {"summary": {}, "orders": [], "request_params": {}}

        args = parser.parse_args(["fliggy-order-list", "list"])
        args.handler(args)

        mock_collect.assert_called_once_with(
            page_num=1,
            page_size=10,
            biz_type=0,
            sort_field_enum="ORDER_CREATE_TIME_DESC",
            deal_start="2026-04-20 00:00:00",
            deal_end="2026-04-20 23:59:59",
            all_pages=False,
        )

    @mock.patch("tourism_automation.collectors.fliggy_order_list.cli.collect_order_list")
    def test_order_list_list_accepts_explicit_deal_range(self, mock_collect):
        parser = build_parser()
        mock_collect.return_value = {"summary": {}, "orders": [], "request_params": {}}

        args = parser.parse_args(
            [
                "fliggy-order-list",
                "list",
                "--deal-start",
                "2026-04-07 00:00:00",
                "--deal-end",
                "2026-04-07 23:59:39",
            ]
        )
        args.handler(args)

        mock_collect.assert_called_once_with(
            page_num=1,
            page_size=10,
            biz_type=0,
            sort_field_enum="ORDER_CREATE_TIME_DESC",
            deal_start="2026-04-07 00:00:00",
            deal_end="2026-04-07 23:59:39",
            all_pages=False,
        )

    @mock.patch("tourism_automation.collectors.fliggy_order_list.cli.collect_order_list")
    def test_order_list_list_passes_all_pages_flag(self, mock_collect):
        parser = build_parser()
        mock_collect.return_value = {"summary": {}, "rows": []}

        args = parser.parse_args(
            [
                "fliggy-order-list",
                "list",
                "--all-pages",
                "--page-size",
                "20",
            ]
        )
        args.handler(args)

        mock_collect.assert_called_once_with(
            page_num=1,
            page_size=20,
            biz_type=0,
            sort_field_enum="ORDER_CREATE_TIME_DESC",
            deal_start=mock.ANY,
            deal_end=mock.ANY,
            all_pages=True,
        )

    def test_shop_kpi_export_no_longer_accepts_password_argument(self):
        parser = build_parser()

        with self.assertRaises(SystemExit):
            parser.parse_args(["shop-kpi-export", "--password", "5678"])

    @mock.patch("tourism_automation.collectors.fliggy_kpi.shop_kpi.cli.export_shop_kpi")
    def test_shop_kpi_export_passes_report_and_day_date_options(self, mock_export):
        parser = build_parser()
        mock_export.return_value = "/tmp/shop.xlsx"

        args = parser.parse_args(
            [
                "shop-kpi-export",
                "--report-name",
                "人均日接入",
                "--date-mode",
                "day",
                "--date",
                "2026-04-20",
            ]
        )
        exit_code = args.handler(args)

        self.assertEqual(exit_code, 0)
        mock_export.assert_called_once_with(
            output_file=None,
            report_name="人均日接入",
            date_mode="day",
            date="2026-04-20",
        )

    @mock.patch("tourism_automation.collectors.fliggy_kpi.shop_kpi.cli.prepare_payload")
    @mock.patch("tourism_automation.collectors.fliggy_kpi.shop_kpi.cli.export_shop_kpi")
    def test_shop_kpi_export_json_outputs_unified_payload(self, mock_export, mock_prepare_payload):
        parser = build_parser()
        mock_export.return_value = "/home/kk/下载/report.xlsx"
        mock_prepare_payload.return_value = {
            "summary": {
                "source": "shop_kpi_excel",
                "report_name": "人均日接入",
                "file_path": "/home/kk/下载/report.xlsx",
                "row_count": 1,
            },
            "rows": [{"客服昵称": "alice"}],
        }
        stdout = io.StringIO()

        args = parser.parse_args(
            [
                "shop-kpi-export",
                "--report-name",
                "人均日接入",
                "--date-mode",
                "day",
                "--date",
                "2026-04-20",
                "--json",
            ]
        )
        with mock.patch("sys.stdout", stdout):
            exit_code = args.handler(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout.getvalue()),
            mock_prepare_payload.return_value,
        )
        mock_export.assert_called_once_with(
            output_file=None,
            report_name="人均日接入",
            date_mode="day",
            date="2026-04-20",
        )
        mock_prepare_payload.assert_called_once_with("/home/kk/下载/report.xlsx")

    def test_shop_kpi_export_defaults_to_renjunrijieru_and_excludes_zhoujixiao(self):
        parser = build_parser()

        args = parser.parse_args(["shop-kpi-export"])

        self.assertEqual(args.report_name, "人均日接入")
        self.assertEqual(args.date_mode, "day")
        self.assertFalse(args.json)
        self.assertEqual(
            parser.parse_args(["shop-kpi-export", "--report-name", "人均日接入"]).report_name,
            "人均日接入",
        )
        self.assertTrue(parser.parse_args(["shop-kpi-export", "--json"]).json)
        with self.assertRaises(SystemExit):
            parser.parse_args(["shop-kpi-export", "--report-name", "周绩效店铺"])

    @mock.patch("tourism_automation.collectors.fliggy_kpi.shop_kpi.cli.export_shop_kpi")
    def test_shop_kpi_export_batch_exports_all_supported_reports(self, mock_export):
        parser = build_parser()
        mock_export.side_effect = [
            "/tmp/renjun.xlsx",
            "/tmp/meizhou.xlsx",
            "/tmp/kefu.xlsx",
        ]

        args = parser.parse_args(
            [
                "shop-kpi-export-batch",
                "--date-mode",
                "day",
                "--date",
                "2026-04-20",
            ]
        )
        exit_code = args.handler(args)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            mock_export.call_args_list,
            [
                mock.call(
                    output_file=None,
                    report_name="人均日接入",
                    date_mode="day",
                    date="2026-04-20",
                ),
                mock.call(
                    output_file=None,
                    report_name="每周店铺个人数据",
                    date_mode="day",
                    date="2026-04-20",
                ),
                mock.call(
                    output_file=None,
                    report_name="客服数据23年新",
                    date_mode="day",
                    date="2026-04-20",
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()

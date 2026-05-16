import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DailyTargetTablesTests(unittest.TestCase):
    def test_daily_sql_targets_current_schemas(self):
        order_sql = load_module("prepare_order_list_sql", "bin/prepare_order_list_sql.py")
        daily_key_sql = load_module("prepare_shop_daily_key_sql", "bin/prepare_shop_daily_key_sql.py")
        sycm_flow_sql = load_module("prepare_sycm_flow_sql", "bin/prepare_sycm_flow_sql.py")
        customer_daily_sql = load_module(
            "prepare_customer_service_data_daily_sql",
            "bin/prepare_customer_service_data_daily_sql.py",
        )

        self.assertEqual(order_sql.TARGET_TABLE, "Xiangwang.order_list")
        self.assertIn(
            "Xiangwang.shop_daily_key_data",
            daily_key_sql.build_upsert_sql(
                {
                    "summary": {
                        "deal_start": "2026-05-01 00:00:00",
                        "total_page": 1,
                        "total_booking": 1,
                        "total_pax": 2,
                        "gmv": 3,
                    },
                    "rows": [],
                }
            ),
        )
        self.assertIn(
            "Xiangwang.shop_data_daily_registration",
            sycm_flow_sql.build_upsert_sql(
                {
                    "summary": {"biz_date": "2026-05-01"},
                    "rows": [{"访客数": 1, "浏览量": 2, "广告流量": 3, "平台流量": 4, "关注店铺人数": 5}],
                }
            ),
        )
        self.assertIn(
            "Xiangwang.customer_service_data_daily",
            customer_daily_sql.build_upsert_sql(
                {
                    "summary": {
                        "report_name": "人均日接入",
                        "file_path": "/tmp/自定义报表_人均日接入_2026-05-01至2026-05-01.xlsx",
                    },
                    "rows": [],
                }
            ),
        )

    def test_repository_has_no_legacy_target_names(self):
        qianniu = "qian" + "niu"
        feizhu = "fei" + "zhu"
        fliggy_customer_service = "fliggy_customer" + "_service"
        sycm = "sy" + "cm"
        forbidden_text = [
            f"prepare_{qianniu}",
            f"prepare_{fliggy_customer_service}",
            "prepare_fliggy_order" + "_list_sql",
            "prepare_fliggy_order" + "_list_for_storage",
            f"{qianniu}.",
            f"{qianniu}_",
            f"mysql {qianniu}",
            f"mysql {feizhu}",
            f"{feizhu}.fliggy_",
            f"{fliggy_customer_service}_",
            f"{sycm}_homepage_",
            f"{sycm}_collection_",
            f"{sycm}_api_raw_",
            f'"database": "{sycm}"',
            f"'database': '{sycm}'",
        ]
        checked_roots = [
            ROOT / "AGENTS.md",
            ROOT / "CLAUDE.md",
            ROOT / "README.md",
            ROOT / "bin",
            ROOT / "docs",
            ROOT / "scripts",
            ROOT / "skills",
            ROOT / "src",
            ROOT / "tests",
        ]
        skipped_dirs = {".git", "__pycache__"}
        paths = []
        for root in checked_roots:
            if root.is_file():
                paths.append(root)
                continue
            paths.extend(path for path in root.rglob("*") if path.is_file() and not skipped_dirs.intersection(path.parts))

        offenders = []
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            if qianniu in relative or f"prepare_{fliggy_customer_service}" in relative:
                offenders.append(f"{relative}: legacy path")
                continue
            if "prepare_fliggy_order" + "_list_sql" in relative or "prepare_fliggy_order" + "_list_for_storage" in relative:
                offenders.append(f"{relative}: legacy path")
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in forbidden_text:
                if token in content:
                    offenders.append(f"{relative}: {token}")

        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()

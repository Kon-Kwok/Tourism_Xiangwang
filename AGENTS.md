# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives in `src/tourism_automation/`. Use `cli/` for command registration, `collectors/` for data collectors such as `sycm/`, `fliggy_home/`, and `fliggy_kpi/`, and `shared/` for reusable Chrome, HTTP, CDP, and result-handling utilities. Tests live in `tests/` and mirror the runtime layout, for example `tests/cli/test_main.py` and `tests/collectors/test_sycm.py`. Operational scripts are in `bin/`; project and usage docs are in `docs/`; start with `docs/README.md` before adding or restructuring docs. SQL assets belong in `sql/`.

## Build, Test, and Development Commands
Run commands from the repository root.

- `python3 -m unittest discover tests`: run the full test suite.
- `python3 -m unittest tests.cli.test_main`: run one CLI-focused test module.
- `python3 -m unittest tests.test_refactored_clients`: validate shared client refactors.
- `python3 -m tourism_automation.cli.main sycm healthcheck`: verify SYCM collector readiness.
- `python3 -m tourism_automation.cli.main sycm collect-home --date 2026-04-21`: collect SYCM homepage metrics for a date.
- `python3 -m tourism_automation.cli.main fliggy-home collect-home --date 2026-04-21`: collect Fliggy homepage metrics.
- `python3 -m tourism_automation.cli.main fliggy-kpi employee --date 2026-04-21 --method api`: collect employee KPI data through the shared debug Chrome session.
- `./bin/start-chrome-unified.sh`: start the shared Chrome debug session required by browser-backed collectors.

## Coding Style & Naming Conventions
Follow Python 3.10+ conventions: 4-space indentation, `snake_case` for modules, functions, and variables, `PascalCase` for classes, and clear English identifiers in code even when business terms are Chinese. Keep collector modules focused: `collector.py`, `client.py`, `normalize.py`, `storage.py`, and `cli.py` when applicable. Prefer small helper functions in `shared/` rather than duplicating Chrome or HTTP logic across collectors.

## Testing Guidelines
This repository uses `unittest`. Add or update tests with every behavior change, especially for CLI argument handling, API normalization, and storage boundaries. Name new files `test_<feature>.py` and keep test fixtures close to the module they validate. Run the narrowest affected test first, then `python3 -m unittest discover tests` before finishing work.

## Commit & Pull Request Guidelines
Use concise, task-focused commit subjects that describe the current change, not repository history. A good pattern is `<area>: <what changed>`, for example `sycm: tighten homepage metric parsing`. Pull requests should include a short summary, affected commands or collectors, verification steps you ran, and screenshots only when UI automation behavior or exported files changed.

## Security & Operations Notes
Do not commit cookies, local Chrome profiles, database dumps, or secrets. Browser automation depends on the long-lived debug Chrome session on port `9222`; reuse it instead of creating ad hoc profiles or closing the shared session during development. Prefer the shared `start-chrome-unified.sh` flow over task-specific browser profiles unless the repository is explicitly updated to support a new mode.

## Project-Specific Data Notes
All daily collection writes in this repository target the unified `Xiangwang` schema and the tables defined in `sql/Xiangwang/Xiangwang.sql`. The current daily key table is `Xiangwang.shop_daily_key_data`; merge scripts use `UPDATE` followed by `INSERT ... WHERE NOT EXISTS` because the live `日期` index may be non-unique. Do not switch these pipelines back to `ON DUPLICATE KEY UPDATE` unless a unique key on `日期` has been verified. 飞猪订单汇总字段 `total_bookings`、`total_pax`、`gmv` require the extra conversion step `prepare_order_list_for_storage.py` -> `prepare_shop_daily_key_sql.py`, and order collection must use `--all-pages`.

## Alimama Advertising Metric Formulas
For 阿里妈妈投放 daily tables such as 明星店铺, 直通车, 引力魔方, 万相台, and 万相台2, use these Excel-compatible formulas:

- `CTR 点击率 = Click / IMP`
- `CPC 点击成本 = Cost / Click`
- `CPM 拉新成本 = (Cost / IMP) * 1000`
- `ROI 投资回报率 = Sales / Cost`
- `CVR 点击转化率 = Order / Click`
- `收藏加购成本 = Cost / (ShoppingCart + Bookmark-Product)`
- `收藏加购量 = ShoppingCart + Bookmark-Product`
- `收藏加购率 = 收藏加购量 / Click`


### 密码信息
- **sudo密码**: `1`
- **MySQL连接方式**: 

主机地址: 172.28.190.60  (WSL当前IP)
端口: 3306
用户名: remote_user
密码: Tourism2024

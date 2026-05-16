# Errors

Command failures and integration errors.

---

## [ERR-20260421-001] mysql-shell-quoting

**Logged**: 2026-04-21T23:25:00+08:00
**Priority**: medium
**Status**: pending
**Area**: backend

### Summary
Inline MySQL DDL failed because shell backtick expansion corrupted the SQL before execution.

### Error
```text
/bin/bash: 行 1: 日期: 未找到命令
ERROR 1064 (42000) at line 1: You have an error in your SQL syntax
```

### Context
- Command/operation attempted: `ALTER TABLE` to replace the date index with a unique key on `日期`
- Input or parameters used: SQL embedded inside a double-quoted shell command
- Environment details if relevant: bash shell, mysql CLI
- Summary or redacted excerpt of relevant output: shell consumed the backtick-quoted identifier before MySQL received the statement

### Suggested Fix
Use a single-quoted heredoc such as `mysql <<'SQL' ... SQL` for statements containing backtick-quoted identifiers.

### Metadata
- Reproducible: yes
- Related Files: .learnings/LEARNINGS.md

---

## [ERR-20260421-002] fliggy-order-list-transient-search-failure

**Logged**: 2026-04-21T23:52:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
The full order ingestion pipeline wrote zeroed daily metrics because the upstream order-list endpoint intermittently returned a transient business failure that looked like an empty result.

### Error
```text
{"success":false,"errorMsg":"订单搜索失败，请稍后再试","orderList":[],"total":0,"totalPage":0}
```

### Context
- Command/operation attempted: `python3 -m tourism_automation.cli.main fliggy-order-list list --all-pages ... | python3 bin/prepare_order_list_for_storage.py | python3 bin/prepare_shop_daily_key_sql.py | python3 bin/exec_mysql_sql.py`
- Input or parameters used: `2026-04-20 00:00:00` to `2026-04-20 23:59:39`
- Environment details if relevant: live Fliggy order-list HTTP endpoint using Chrome-backed cookies
- Summary or redacted excerpt of relevant output: the same request succeeded on a later retry and returned 18 orders, proving the zero result was transient failure rather than genuine no-data

### Suggested Fix
Retry the order-list request when the parsed business payload returns `success=false` with the known transient failure message, and only normalize after a successful response or final exhausted attempt.

### Metadata
- Reproducible: yes
- Related Files: src/tourism_automation/collectors/fliggy_order_list/client.py, tests/collectors/test_fliggy_order_list.py
- See Also: LRN-20260421-004

---

## [ERR-20260422-001] qianniu-shop-data-daily-registration-null-follow-count

**Logged**: 2026-04-22T00:00:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
The daily-registration SQL builder crashed when yesterday’s flow-monitor payload returned `关注店铺人数 = null`.

### Error
```text
ValueError: invalid integer value: None
```

### Context
- Command/operation attempted: `python3 -m tourism_automation.cli.main sycm flow-monitor --date 2026-04-21 --shop-name 'SYCM' | python3 bin/prepare_shop_data_daily_registration_sql.py | python3 bin/exec_mysql_sql.py`
- Input or parameters used: 2026-04-21 yesterday-report pipeline
- Environment details if relevant: live SYCM flow-monitor payload returned a single row with all metric fields `null`
- Summary or redacted excerpt of relevant output: `prepare_shop_data_daily_registration_sql.py` attempted `Decimal(str(None))` and aborted before SQL execution

### Suggested Fix
Treat `None` as `0` for `关注店铺人数` so the registration table stays aligned with the existing flow-monitor numeric-null handling.

### Metadata
- Reproducible: yes
- Related Files: bin/prepare_shop_data_daily_registration_sql.py, tests/test_prepare_shop_data_daily_registration_sql.py
- See Also: LRN-20260422-001

---

## [ERR-20260422-002] empty-topchitu-report-treated-as-failure

**Logged**: 2026-04-22T00:05:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
The customer-service SQL builders treated valid empty KPI exports as fatal errors, blocking the full yesterday-report workflow.

### Error
```text
ValueError: no customer rows found for insertion
```

### Context
- Command/operation attempted: `python3 -m tourism_automation.cli.main shop-kpi-export --report-name '人均日接入' --date-mode day --date 2026-04-21 --json | python3 bin/prepare_customer_service_data_daily_sql.py | python3 bin/exec_mysql_sql.py`
- Input or parameters used: 2026-04-21 yesterday-report pipeline
- Environment details if relevant: exported JSON was valid and contained `row_count = 0`, `rows = []`
- Summary or redacted excerpt of relevant output: SQL generation aborted even though the export succeeded and the correct semantic result for the date was “no rows”

### Suggested Fix
Emit a date-scoped `DELETE` when the report is empty and let orchestration validation accept `COUNT(*) = 0` for empty daily exports.

### Metadata
- Reproducible: yes
- Related Files: bin/prepare_customer_service_data_daily_sql.py, bin/prepare_customer_service_performance_workload_sql.py, bin/prepare_customer_service_performance_summary_sql.py, /home/kk/.codex/skills/yesterday-report-ingestion/scripts/run_yesterday_report.py
- See Also: LRN-20260422-002

---

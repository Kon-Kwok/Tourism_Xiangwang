# Tourism Xiangwang 日报采集

本仓库用于采集并入库 Xiangwang 日报数据。当前主流程覆盖赤兔 KPI、飞猪订单、SYCM 流量看板、阿里妈妈投放日报、赤兔团队看板、二次预约订单，并支持把指定日期的数据库数据导出为 Excel（含「店铺关键数据完成情况」汇总 sheet）。

> **当前分支**: `feature/shop-kpi-sheet` — 新增店铺关键数据完成情况 sheet 及配套采集能力，待业务验证后合并 main。

## 主要入口

```bash
# 启动统一 Chrome 调试窗口
./bin/start-chrome-unified.sh

# 一键采集昨日全部日报（含新增的团队看板和二次预约）
./scripts/all.sh

# 一键采集指定日期
./scripts/all.sh 2026-05-02

# 单独采集
./scripts/kpi_reports.sh 2026-05-02          # 赤兔 KPI 三个报表
./scripts/fliggy_orders.sh 2026-05-02         # 飞猪订单列表
./scripts/sycm_flow.sh 2026-05-02             # SYCM 流量看板
./scripts/alimama_daily.sh 2026-05-02         # 阿里妈妈投放日报
./scripts/team_dashboard.sh 2026-05-02        # 赤兔团队看板（首响/平响）★新增
python3 -m tourism_automation.cli.main fliggy-secondary-order collect \
  --start-date 2026-05-02 --end-date 2026-05-02  # 二次预约订单 ★新增

# 导出指定日期 Excel（含「店铺关键数据完成情况」sheet ★新增）
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --date 2026-05-02 \
  --host 127.0.0.1 --port 3307 --user root --password xxx --database Xiangwang \
  --output exports/daily.xlsx

# 导出整月数据
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --start 2026-05-01 --end 2026-05-31 \
  --host 127.0.0.1 --port 3307 --user root --password xxx --database Xiangwang \
  --output exports/monthly.xlsx
```

## 数据范围

| 业务 | 目标表 |
| --- | --- |
| 赤兔 KPI | `customer_service_data_daily`、`customer_service_performance_summary`、`customer_service_performance_workload_analysis` |
| 飞猪订单 | `order_list`、`shop_daily_key_data` |
| SYCM 流量 | `shop_daily_key_data`、`shop_data_daily_registration` |
| 阿里妈妈投放 | `star_store`、`tmall_express`、`gravity_rubiks_cube`、`wanxiangtai`、`wanxiangtai_2` |
| 赤兔团队看板 ★ | `team_dashboard_daily` — 首次响应时间、平均响应时间 |
| 二次预约订单 ★ | `order_list_secondary` — 二次预约出行订单 |

## 新增：店铺关键数据完成情况 Sheet ★

导出 Excel 时自动生成「店铺关键数据完成情况」sheet，包含六大板块：

| 板块 | 指标 | 数据来源 |
|------|------|----------|
| 店铺数据 | Total UV / Paid UV / Paid Cost / Total BK / Paid BK / Paid ROI | shop_daily_key_data + shop_data_daily_registration + 阿里妈妈四表 |
| 客服数据 | 咨询人数 / 接待人数 / 首响 / 平响 / 订单数 | shop_data_daily_registration + customer_service_performance_summary + team_dashboard_daily |
| 月度预算消耗 | 每月预算 / 实际消耗 / 转化单量 | 固定值 + 阿里妈妈四表财务月(21号-20号)聚合 |
| MTD / YTD | 完成量 / 完成率 / 投放消耗 / 投放转化 | Excel 公式引用（PAX→自然月, 阿里妈妈→财务月） |
| 年度完成情况 | 2026 target / Actual PAX / 完成率 | 固定 target + Step1(order_list 自然月聚合) + Step2(order_list_secondary 自然月聚合) |
| 条件格式 | 涨绿跌红(含 +/- 符号)，响应时间反转 | 代码实现 |

**PAX 计算口径：**
- **Step1**：`order_list`，自然月，排除 `status_text IN ('交易关闭','等待买家付款')`，排除 `package_type` 含 16 个关键词（补差/补、尾款、升级/升/升房/升舱、税费/补税、改期/改/改航线、加人/加、生日礼遇、通兑），`SUM(buy_mount)` = PAX
- **Step2**：`order_list_secondary`，自然月，排除 `status_text = '商家已驳回'`，按 `order_id` 去重（唯一键），`SUM(buy_mount)` = PAX（pcount 字段，不乘 Q）
- **月度 PAX = Step1 + Step2**

**月份口径：**
- PAX（C30:C41）：自然月（1号至月末）
- 阿里妈妈消耗/转化（Row 25-26）：财务月（21号至次月20号）
- MTD Row 13-14：自然月索引 → PAX
- MTD Row 15-16：财务月索引 → 阿里妈妈

**导出参数：**
```bash
# 指定 KPI 对比日期（与数据范围解耦）
--kpi-date 2026-06-30

# 优先级: --kpi-date > --date > --end > 自动检测
```

核心实现文件：`scripts/fill_shop_kpi_sheet.py`

> **业务验证状态**：5月 PAX=813（与业务完全一致 ✅），6月已核验通过 ✅

## 采集流程

```text
all.sh
├── 业务1: 赤兔KPI三个报表      → kpi_reports.sh
├── 业务2: 飞猪订单列表          → fliggy_orders.sh
├── 业务3: SYCM流量看板          → sycm_flow.sh
├── 业务4: 阿里妈妈投放日报      → alimama_daily.sh
├── 业务5: 跨表规则应用          → apply_cross_table_rules.sh
├── 业务6: 赤兔团队看板 ★新增    → team_dashboard.sh → CDP → 赤兔 team-kpi API
└── 业务7: 二次预约订单 ★新增    → fliggy-secondary-order collect → CDP → yuyue.fliggy.com
```

## 环境配置

项目根目录 `.env` 会被脚本自动读取：

```bash
HOST=127.0.0.1
PORT=3307
USER=root
PASS=your_mysql_password
```

浏览器采集依赖统一 Chrome 调试会话，端口 `9222`。采集前确认 Chrome 已登录以下网站：
- `sycm.taobao.com` — 生意参谋
- `fsc.fliggy.com` — 飞猪商家工作台
- `kf.topchitu.com` — 赤兔名品
- `brandsearch.taobao.com` — 品销宝
- `one.alimama.com` — 万相台
- `yuyue.fliggy.com` — 飞猪预约管理（二次预约采集需要）★新增

## 项目结构

```text
src/tourism_automation/         # CLI、采集器和共享客户端
  collectors/
    fliggy_secondary_order/     # 二次预约订单采集 ★新增
bin/                            # 数据转换和 Chrome 辅助脚本
  prepare_team_dashboard.py     # 团队看板采集 ★新增
  backfill_team_dashboard.py    # 团队看板历史回填 ★新增
scripts/                        # 日报采集编排脚本
  fill_shop_kpi_sheet.py        # KPI sheet 核心填充逻辑 ★新增
  team_dashboard.sh             # 团队看板 Shell 包装 ★新增
skills/skills/                  # OpenClaw/Codex 技能和 Excel 导出脚本
docs/                           # 架构、采集器和运维文档
sql/Xiangwang/                  # Xiangwang 建表 SQL
tests/                          # unittest 测试
exports/                        # Excel 导出文件
```

## 开发命令

```bash
python3 -m unittest discover tests
python3 -m unittest tests.cli.test_main
python3 -m unittest tests.test_refactored_clients
```

## 注意事项

- 飞猪订单采集必须使用 `--all-pages`。
- `shop_daily_key_data` 的 `日期` 索引可能非唯一，写入保持 `UPDATE` 后 `INSERT ... WHERE NOT EXISTS`。
- 二次预约采集需确保 `yuyue.fliggy.com` 页面在 Chrome 中已打开，否则 `find_tab_by_url_pattern` 会报错。
- 2026Actual PAX = Step1（order_list 关键词过滤） + Step2（order_list_secondary 排除商家已驳回），Step2 取 `buy_mount`（API pcount 字段），不乘 Q。业务已核验确认。
- 不要提交 cookies、本地 Chrome profile、数据库 dump 或真实密钥。

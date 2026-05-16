# Tourism Xiangwang 日报采集

本仓库用于采集并入库 Xiangwang 日报数据。当前主流程覆盖赤兔 KPI、飞猪订单、SYCM 流量看板和阿里妈妈投放日报，并支持把指定日期的数据库数据导出为 Excel。

## 主要入口

```bash
# 启动统一 Chrome 调试窗口
./bin/start-chrome-unified.sh

# 一键采集昨日四大日报
./scripts/all.sh

# 一键采集指定日期
./scripts/all.sh 2026-05-02

# 单独采集
./scripts/kpi_reports.sh 2026-05-02
./scripts/fliggy_orders.sh 2026-05-02
./scripts/sycm_flow.sh 2026-05-02
./scripts/alimama_daily.sh 2026-05-02

# 导出指定日期数据库 Excel
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --date 2026-05-02 \
  --output exports/daily_database_2026-05-02.xlsx
```

## 数据范围

| 业务 | 目标表 |
| --- | --- |
| 赤兔 KPI | `customer_service_data_daily`、`customer_service_performance_summary`、`customer_service_performance_workload_analysis` |
| 飞猪订单 | `order_list`、`shop_daily_key_data` |
| SYCM 流量 | `shop_daily_key_data`、`shop_data_daily_registration` |
| 阿里妈妈投放 | `star_store`、`tmall_express`、`gravity_rubiks_cube`、`wanxiangtai`、`wanxiangtai_2` |

赤兔 KPI 日报脚本现在通过网页接口读取三个报表，再转换入库。飞猪订单采集会写订单明细，并把 `total_bookings`、`total_pax`、`gmv` 汇总到 `shop_daily_key_data`。Excel 导出默认生成 `exports/daily_database_YYYY-MM-DD.xlsx`。

## 环境配置

项目根目录 `.env` 会被脚本自动读取：

```bash
HOST=localhost
PORT=3306
USER=remote_user
PASS=your_mysql_password
DATABASE=Xiangwang
```

浏览器采集依赖统一 Chrome 调试会话，端口 `9222`。采集前确认已登录 `sycm.taobao.com`、`fsc.fliggy.com`、`kf.topchitu.com`、`brandsearch.taobao.com` 和 `one.alimama.com`。

## 项目结构

```text
src/tourism_automation/   # CLI、采集器和共享客户端
bin/                      # 数据转换和 Chrome 辅助脚本
scripts/                  # 日报采集编排脚本
skills/skills/            # OpenClaw/Codex 技能和 Excel 导出脚本
docs/                     # 架构、采集器和运维文档
sql/Xiangwang/            # Xiangwang 建表 SQL
tests/                    # unittest 测试
exports/                  # Excel 导出文件
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
- 不要提交 cookies、本地 Chrome profile、数据库 dump 或真实密钥。

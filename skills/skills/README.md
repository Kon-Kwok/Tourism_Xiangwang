# 技能清单

当前仓库保留两个 OpenClaw/Codex 日报相关技能。

## openclaw-daily-data-collection

用途：采集四大日报并写入 `Xiangwang` 数据库。

入口：

```bash
./scripts/all.sh 2026-05-02
```

覆盖业务：

- 赤兔 KPI 客服报表：`customer_service_data_daily`、`customer_service_performance_summary`、`customer_service_performance_workload_analysis`
- 飞猪订单列表：`order_list`、`shop_daily_key_data`
- SYCM 流量看板：`shop_daily_key_data`、`shop_data_daily_registration`
- 阿里妈妈投放日报：`star_store`、`tmall_express`、`gravity_rubiks_cube`、`wanxiangtai`、`wanxiangtai_2`

技能文件：[openclaw-daily-data-collection/SKILL.md](openclaw-daily-data-collection/SKILL.md)

## openclaw-daily-database-excel

用途：从 `Xiangwang` 数据库读取指定日期的日报表数据，并导出 Excel 工作簿。

入口：

```bash
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --date 2026-05-02 \
  --output exports/daily_database_2026-05-02.xlsx
```

默认输出：

```text
exports/daily_database_YYYY-MM-DD.xlsx
```

默认包含 `overview`、赤兔三张客服表、店铺日度关键数据、店铺每日登记和阿里妈妈五张投放表。需要导出库里所有可识别日期列的表时，加 `--all-date-tables`。

技能文件：[openclaw-daily-database-excel/SKILL.md](openclaw-daily-database-excel/SKILL.md)

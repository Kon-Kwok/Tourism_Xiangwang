# 技能清单

当前仓库保留 OpenClaw/Codex 日报和月度汇总相关技能。

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

样式：所有导出 sheet 统一使用阿里妈妈月汇总表风格，表头深蓝 `FF305496`、浅色表头字 `FFF2F2F2`、白底数据区、等线 11 号、居中、细边框。新增导出类技能也应复用这套样式。

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

## export-alimama-monthly-summary

用途：从阿里妈妈投放每日数据工作簿读取日明细，按 2026 年统计周期导出全新的月度汇总工作簿，并复用原工作簿样式。

入口：

```bash
python3 skills/skills/export-alimama-monthly-summary/scripts/update_monthly_summary.py "我要6月的月数据汇总"
```

默认处理：

```text
C:\Users\Gzk\Desktop\2026年阿里妈妈投放每日数据-更新到5.8(2).xlsx
```

支持 `6月`、`六月`、`6月份`、`2026-05-21:2026-06-20` 等输入。月度汇总会统计 `明星店铺`、`直通车`、`引力魔方`、`万相台`；基础汇总按表头写入 `Cost 花费`、`IMP 展示`、`Click 点击`、`Order 订单`、`Sales 销量/GMV`、`ShoppingCart 加入购物车`、`Bookmark-Product 宝贝收藏`、`Bookmark-Store 店铺收藏`、`总收藏数`。派生指标包含 CTR、CPC、CPM、ROI、CVR、ASP、订单成本、加购成本、收藏加购数、收藏加购环比、收藏加购成本、花费环比、点击占比、加购环比、成交环比、加购成本环比、收藏加购成本环比、花费占比、费率；环比公式使用隐藏的上一周期辅助行计算。

技能文件：[export-alimama-monthly-summary/SKILL.md](export-alimama-monthly-summary/SKILL.md)

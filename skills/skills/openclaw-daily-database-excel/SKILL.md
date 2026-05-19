---
name: openclaw-daily-database-excel
description: OpenClaw 侧导出 Xiangwang 数据库当日数据到 Excel。用户需要“当日数据库数据”“全部数据库日报”“导出数据库 Excel”“今天所有表数据”或要求把 Xiangwang 当日数据生成 xlsx 时使用。
---

# OpenClaw 当日数据库 Excel 导出技能

从 `Xiangwang` 数据库读取指定日期相关的日报表数据，并生成一个 Excel 工作簿。每张有当日数据的业务表导出为一个 sheet，另有 `overview` 汇总 sheet 展示导出表的当日行数。

## 快速开始

在项目根目录执行：

```bash
cd ~/Tourism_Xiangwang

# 默认导出今天
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py

# 指定日期
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py --date 2026-05-16

# 指定输出文件
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py --date 2026-05-16 --output exports/xiangwang_2026-05-16.xlsx

# 日期范围合并导出
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py --start 2026-05-01 --end 2026-05-17

# 日期范围 + 指定输出文件
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py --start 2026-05-01 --end 2026-05-17 --output exports/merged.xlsx
```

## 默认输出

未传 `--output` 时，文件写到：

```text
exports/daily_database_YYYY-MM-DD.xlsx
```

## 表格样式

所有导出的 Excel 表格统一复用阿里妈妈月汇总表风格：

- 表头深蓝底：`FF305496`
- 表头浅色字体：`FFF2F2F2`
- 数据区白底、黑字
- 字体：等线，11 号
- 全表水平居中、垂直居中
- 全表细边框
- 表头自动换行，行高 `41.4`

不要为导出表格另造颜色或底色；新增导出脚本也应复用这套样式。

## 数据库连接

脚本会优先读取项目根目录 `.env`：

```bash
HOST=127.0.0.1
PORT=3306
USER=remote_user
PASS=Tourism2024
DATABASE=Xiangwang
```

如果 `.env` 不存在，默认使用：

```text
HOST=127.0.0.1
PORT=3306
USER=remote_user
PASS=Tourism2024
DATABASE=Xiangwang
```

也可以通过命令行覆盖：

```bash
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --date 2026-05-16 \
  --host 127.0.0.1 \
  --port 3306 \
  --user remote_user \
  --password Tourism2024 \
  --database Xiangwang
```

## 导出范围

默认导出这些日报目标表：

- `customer_service_data_daily`，日期列 `日期`
- `customer_service_performance_summary`，日期列 `date_time`
- `customer_service_performance_workload_analysis`，日期列 `date_time`
- `shop_daily_key_data`，日期列 `日期`
- `shop_data_daily_registration`，日期列 `日期`
- `star_store`，日期列 `date_time`
- `tmall_express`，日期列 `date_time`
- `gravity_rubiks_cube`，日期列 `date_time`
- `wanxiangtai`，日期列 `date_time`
- `wanxiangtai_2`，日期列 `date_time`

如果要导出库里所有存在日期列且当日有数据的表，加 `--all-date-tables`。脚本会自动识别 `日期`、`date_time`、`order_date`、`biz_date` 等常见日期列。

默认跳过当日 `0` 行的空表，不创建空 sheet。

## 使用规则

- 用户说”当日””今天”时，不传日期，脚本默认今天。
- 用户给出单个日期时，使用 `--date YYYY-MM-DD`。
- 用户给出日期范围”xx到xx”时，使用 `--start YYYY-MM-DD --end YYYY-MM-DD`。
- 导出前不自动采集数据；当日表为空时默认不导出该表。
- 用户要求“只导出入库过的表”“不要空表”时，保持默认行为，不加 `--include-empty-tables`。
- 需要先采集日报时，先使用 `openclaw-daily-data-collection` 技能运行采集，再运行本技能导出 Excel。

---
name: export-alimama-monthly-summary
description: Create or update Alimama advertising monthly summary Excel blocks for Xiangwang workbooks. Use when the user asks to export, append, update, or generate 阿里妈妈/月数据汇总/monthly advertising summary tables from daily sheets, especially for the 2026 periods 1/1-1/20, monthly 21st-20th cycles, and the year-end 11/21-12/31 cycle.
---

# Export Alimama Monthly Summary

Use this skill to create a new standalone monthly summary workbook from an Alimama advertising workbook such as `2026年阿里妈妈投放每日数据-更新到5.8(2).xlsx`.

## Quick Start

Run the bundled script from any directory. With no arguments it uses the default Windows desktop workbook and exports the next period after the latest monthly block:

```bash
python3 ~/.codex/skills/export-alimama-monthly-summary/scripts/update_monthly_summary.py
```

If the user names a specific cycle, pass only that cycle:

```bash
python3 ~/.codex/skills/export-alimama-monthly-summary/scripts/update_monthly_summary.py 2026-05-21:2026-06-20
```

If the user asks vaguely for a month, pass their words directly. The script recognizes `6月`, `六月`, `6月份`, and `我要6月的月数据汇总`:

```bash
python3 ~/.codex/skills/export-alimama-monthly-summary/scripts/update_monthly_summary.py "我要6月的月数据汇总"
```

The script creates a new workbook on the Windows desktop, for example `alimama_5月月数据汇总.xlsx`. It does not overwrite the source workbook.

## Period Rules

For 2026 monthly reporting:

- January cycle: `2026-01-01` through `2026-01-20`.
- Normal cycles: previous month day 21 through current month day 20, for example `2026-05-21:2026-06-20`.
- Year-end cycle: `2026-11-21` through `2026-12-31`.

If the user gives a period explicitly, use it. If they give only a month label, pass the natural text to the script and state the exact dates before running. Month labels mean the report month by cycle end month: `6月` means `2026-05-21` through `2026-06-20`, and `12月` means `2026-11-21` through `2026-12-31`.

## Workbook Rules

- Use the default workbook `C:\Users\Gzk\Desktop\2026年阿里妈妈投放每日数据-更新到5.8(2).xlsx`.
- Prefer summary sheet `月数据汇总-` as the style/formula template because it has the newer formula area. Fall back to `月数据汇总` only if `月数据汇总-` does not exist.
- Reuse the workbook's existing visual style. Do not invent colors. Copy fills, fonts, font colors, borders, alignment, number formats, row heights, and column widths from the existing template rows/sheets.
- For `月数据汇总-`, use the latest complete block whose base metric columns match the daily sheets. Ignore duplicate or trial tail blocks that do not match the daily data.
- If updating any other sheet in this workbook later, copy styles from the same sheet's existing row/header pattern before writing values.
- Summarize these channels: `明星店铺`, `直通车`, `引力魔方`, `万相台`.
- Identify summary columns by header text, not by fixed Excel letters. Write base totals for these headers when present:
  - Cost 花费
  - IMP 展示
  - Click 点击
  - Order 订单
  - Sales 销量/GMV
  - ShoppingCart 加入购物车
  - Bookmark-Product 宝贝收藏
  - Bookmark-Store 店铺收藏
  - 总收藏数 = Bookmark-Product + Bookmark-Store
- Rebuild derived metric formulas by header meaning:
  - CTR 点击率 = Click / IMP
  - CPC 点击成本 = Cost / Click
  - CPM 千次展现成本 = Cost / IMP * 1000
  - ROI 投资回报率 = Sales / Cost
  - CVR 点击转化率 = Order / Click
  - ASP 订单均价 = IF(Order = 0, 0, Sales / Order)
  - Cporder 订单成本 = IF(Order = 0, 0, Cost / Order)
  - CPshopping cart 加购成本 = Cost / ShoppingCart
  - 收藏加购数 = ShoppingCart + 总收藏数
  - 收藏加购成本 = Cost / 收藏加购数
  - 花费占比 = channel Cost / total Cost
  - 费率 = total Cost / total Sales
- For month-over-month fields, include hidden previous-period helper rows in the new workbook:
  - 收藏加购环比
  - 花费环比
  - 加购环比
  - 成交环比
  - 加购成本环比
  - 收藏加购成本环比
- For 点击占比, calculate channel Click / current total Click.

## Script Behavior

The script:

1. Opens the workbook with `openpyxl`.
2. Finds each daily channel sheet and filters rows by the date column.
3. Sums the metric columns by header names rather than fixed column letters or row numbers.
4. Finds the latest valid template block by checking that the base metric columns match the daily detail sheets.
5. Creates a new workbook with one visible monthly summary sheet.
6. Copies formatting, row heights, column widths, number formats, borders, alignment, font colors, and fills from the template block.
7. Writes current-period rows and hidden previous-period helper rows.
8. Rebuilds all derived formulas, including the month-over-month columns.
9. Writes the workbook and prints the output path plus row counts per channel.

Keep the interface simple. Do not add flags unless the user explicitly asks for a different workbook or output path.

## Validation

After writing a workbook, reopen it and verify:

- The new block label matches the requested cycle, such as `5月21号-6月20号`.
- `明星店铺`/`直通车`/`引力魔方`/`万相台` have numeric totals under the base metric headers.
- Derived metric headers such as CTR/CPC/CPM/ROI/CVR/ASP/订单成本/加购成本/收藏加购数/收藏加购环比/收藏加购成本/花费环比/点击占比/加购环比/成交环比/加购成本环比/收藏加购成本环比/花费占比/费率 contain formulas, not static numbers.
- Previous-period helper rows are hidden and provide the basis for 环比 formulas.
- The workbook can be opened by Excel and formulas recalculate normally.

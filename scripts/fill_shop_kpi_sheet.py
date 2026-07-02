#!/usr/bin/env python3
"""Fill the 店铺关键数据完成情况 sheet with data from Xiangwang DB."""
from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

SHEET_NAME = "店铺关键数据完成情况"

# Colors
DARK_BLUE_FILL = PatternFill(start_color="FF002060", end_color="FF002060", fill_type="solid")
WHITE_FONT_BOLD = Font(name="等线", size=10, bold=True, color="FFFFFFFF")
NORMAL_FONT = Font(name="等线", size=11)
NORMAL_FONT_10 = Font(name="等线", size=10)
NORMAL_FONT_10_BOLD = Font(name="等线", size=10, bold=True)
THIN_BORDER = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
BLACK_FONT = Font(name="等线", size=11, color="FF000000")

# Fixed budget values (Row 24, columns B-M) — business reference, update annually
MONTHLY_BUDGET = [180000, 165000, 250000, 200000, 250000, 250000,
                  200000, 200000, 165000, 300000, 250000, 165000]

# Monthly targets (B30-B41) — business reference, update annually
MONTHLY_TARGETS = [682, 529, 909, 793, 1057, 1110, 962, 996, 737, 1586, 805, 408]

# Fiscal month labels (Row 23): Jan(1/1-1/20) through Dec(11/21-12/31)
FISCAL_MONTH_LABELS = [
    "Jan\n1/1-1/20", "Feb\n1/21-2/20", "Mar\n2/21-3/20",
    "Apr\n3/21-4/20", "May\n4/21-5/20", "Jun\n5/21-6/20",
    "Jul\n6/21-7/20", "Aug\n7/21-8/20", "Sep\n8/21-9/20",
    "Oct\n9/21-10/20", "Nov\n10/21-11/20", "Dec\n11/21-12/31",
]

# Month short labels (Row 30-41)
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NUMERIC_TEXT_RE = re.compile(r"^[¥￥]?([+-]?[\d,]+(?:\.\d*)?)$")


def get_fiscal_month_bounds(year: int) -> list[tuple[str, str]]:
    """Fiscal month boundaries: each month = 21st of prev month to 20th of current.

    Jan is special (1/1-1/20), Dec wraps to next year (11/21-12/31).
    Used for alimama spend/orders (Row 25-26) and MTD alimama refs (Row 15-16).
    """
    return [
        (f"{year}-01-01", f"{year}-01-21"),     # Jan:  1/1  - 1/20
        (f"{year}-01-21", f"{year}-02-21"),     # Feb:  1/21 - 2/20
        (f"{year}-02-21", f"{year}-03-21"),     # Mar:  2/21 - 3/20
        (f"{year}-03-21", f"{year}-04-21"),     # Apr:  3/21 - 4/20
        (f"{year}-04-21", f"{year}-05-21"),     # May:  4/21 - 5/20
        (f"{year}-05-21", f"{year}-06-21"),     # Jun:  5/21 - 6/20
        (f"{year}-06-21", f"{year}-07-21"),     # Jul:  6/21 - 7/20
        (f"{year}-07-21", f"{year}-08-21"),     # Aug:  7/21 - 8/20
        (f"{year}-08-21", f"{year}-09-21"),     # Sep:  8/21 - 9/20
        (f"{year}-09-21", f"{year}-10-21"),     # Oct:  9/21 - 10/20
        (f"{year}-10-21", f"{year}-11-21"),     # Nov:  10/21 - 11/20
        (f"{year}-11-21", f"{year+1}-01-01"),    # Dec:  11/21 - 12/31
    ]


def get_natural_month_bounds(year: int) -> list[tuple[str, str]]:
    """Natural (calendar) month boundaries for PAX aggregation."""
    next_year = year + 1
    return [
        (f"{year}-01-01", f"{year}-02-01"), (f"{year}-02-01", f"{year}-03-01"),
        (f"{year}-03-01", f"{year}-04-01"), (f"{year}-04-01", f"{year}-05-01"),
        (f"{year}-05-01", f"{year}-06-01"), (f"{year}-06-01", f"{year}-07-01"),
        (f"{year}-07-01", f"{year}-08-01"), (f"{year}-08-01", f"{year}-09-01"),
        (f"{year}-09-01", f"{year}-10-01"), (f"{year}-10-01", f"{year}-11-01"),
        (f"{year}-11-01", f"{year}-12-01"), (f"{year}-12-01", f"{next_year}-01-01"),
    ]


def parse_money(value: Any) -> float:
    """Parse '¥1,234.56' or 1234.56 or Decimal to float."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    if isinstance(value, str):
        m = NUMERIC_TEXT_RE.match(value.strip())
        if m:
            return float(m.group(1).replace(",", ""))
        return 0.0
    return 0.0


def build_sheet_structure(ws, year: int = 2026):
    """Create the full template structure (labels, headers, merges, formatting)."""
    # --- Row 1: Date label ---
    ws["A1"] = "Date"
    ws["A1"].font = NORMAL_FONT
    ws["A1"].alignment = Alignment(vertical="center")
    _apply_border(ws["A1"])

    # --- Rows 4-6: 店铺数据 ---
    shop_headers = {
        "A4": "店铺数据", "B4": "Total UV", "C4": "Paid UV",
        "D4": "Paid Cost", "E4": "TotalBK", "F4": "PaidBK", "G4": "Paid ROI",
    }
    for ref, text in shop_headers.items():
        ws[ref] = text
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])

    ws["A5"] = "VS Yesterday"
    ws["A6"] = "VS LW"
    for ref in ("A5", "A6"):
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])
    for r in range(5, 7):
        for c in range(2, 8):
            cell = ws.cell(row=r, column=c)
            _apply_border(cell)
            cell.alignment = Alignment(vertical="center")

    # --- Rows 8-10: 客服数据 ---
    cs_headers = {
        "A8": "客服数据", "B8": "咨询人数", "C8": "接待人数",
        "D8": "首响", "E8": "平响", "F8": "订单数",
    }
    for ref, text in cs_headers.items():
        ws[ref] = text
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])

    ws["A9"] = "VS Yesterday"
    ws["A10"] = "VS LW"
    for ref in ("A9", "A10"):
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])
    for r in range(9, 11):
        for c in range(2, 7):
            cell = ws.cell(row=r, column=c)
            _apply_border(cell)
            cell.alignment = Alignment(vertical="center")

    # --- Rows 12-19: MTD / YTD ---
    ws.merge_cells("A12:B12")
    ws["A12"] = "Month Target"
    ws["A12"].font = NORMAL_FONT
    ws["A12"].alignment = Alignment(vertical="center")

    mtd_labels = {
        "A13": "MTD完成量:", "A14": "MTD完成率:",
        "A15": "MTD投放(阿里妈妈)消耗总额:", "A16": "MTD投放(阿里妈妈)转化量:",
        "A18": "YTD完成量:", "A19": "YTD完成率:",
    }
    for ref, text in mtd_labels.items():
        ws[ref] = text
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")

    # --- Rows 22-26: 月度预算和消耗进度表 ---
    ws.merge_cells("B22:D22")
    ws.merge_cells("E22:G22")
    ws.merge_cells("H22:J22")
    ws.merge_cells("K22:M22")
    ws.merge_cells("A22:A23")
    ws["A22"] = "月份"
    _set_header_cell(ws["A22"], "月份", wrap=True)
    for col_letter, text in [("B", "Q1"), ("E", "Q2"), ("H", "Q3"), ("K", "Q4")]:
        _set_header_cell(ws[f"{col_letter}22"], text)

    month_cols = list("BCDEFGHIJKLM")
    for i, col_letter in enumerate(month_cols):
        _set_header_cell(ws[f"{col_letter}23"], FISCAL_MONTH_LABELS[i], wrap=True)
    # C,D,F,G,I,J,L,M row 22 are inside merged Q1-Q4 ranges; skip them

    # Row 24: 每月预算
    ws["A24"] = "每月预算"
    ws["A24"].font = NORMAL_FONT_10
    ws["A24"].alignment = Alignment(vertical="center")
    _apply_border(ws["A24"])
    for i, col_letter in enumerate(month_cols):
        cell = ws[f"{col_letter}24"]
        cell.value = MONTHLY_BUDGET[i]
        cell.font = NORMAL_FONT_10
        cell.number_format = '#,##0'
        cell.alignment = Alignment(vertical="center")
        _apply_border(cell)

    # Row 25: 实际消耗
    ws["A25"] = "实际消耗"
    ws["A25"].font = NORMAL_FONT_10
    ws["A25"].alignment = Alignment(vertical="center")
    _apply_border(ws["A25"])
    for col_letter in month_cols:
        cell = ws[f"{col_letter}25"]
        cell.font = NORMAL_FONT_10
        cell.number_format = '#,##0'
        cell.alignment = Alignment(vertical="center")
        _apply_border(cell)

    # Row 26: 转化单量
    ws["A26"] = "转化单量"
    ws["A26"].font = NORMAL_FONT_10
    ws["A26"].alignment = Alignment(vertical="center")
    _apply_border(ws["A26"])
    for col_letter in month_cols:
        cell = ws[f"{col_letter}26"]
        cell.font = NORMAL_FONT_10
        cell.number_format = '#,##0'
        cell.alignment = Alignment(vertical="center")
        _apply_border(cell)

    # --- Rows 29-42: 年度完成情况表 ---
    ws["A29"] = "月份"
    ws["B29"] = f"{year}\ntarget"
    ws["C29"] = f"{year}\nActual"
    ws["D29"] = "完成率"
    for ref in ("A29", "B29", "C29", "D29"):
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])

    for i, (label, target) in enumerate(zip(MONTH_LABELS, MONTHLY_TARGETS)):
        r = 30 + i
        ws[f"A{r}"] = label
        ws[f"A{r}"].font = NORMAL_FONT
        ws[f"B{r}"] = target
        ws[f"B{r}"].font = NORMAL_FONT
        ws[f"B{r}"].number_format = '#,##0'
        ws[f"D{r}"] = f'=IFERROR(C{r}/B{r},"")'
        ws[f"D{r}"].font = NORMAL_FONT
        ws[f"D{r}"].number_format = '0%'
        for c in range(1, 5):
            ws.cell(row=r, column=c).alignment = Alignment(vertical="center")
            _apply_border(ws.cell(row=r, column=c))

    # Row 42: 总计
    ws["A42"] = "总计"
    ws["B42"] = "=SUM(B30:B41)"
    ws["C42"] = "=SUM(C30:C41)"
    ws["D42"] = '=IFERROR(C42/B42,"")'
    for ref in ("A42", "B42", "C42", "D42"):
        ws[ref].font = NORMAL_FONT
        ws[ref].alignment = Alignment(vertical="center")
        _apply_border(ws[ref])
    ws["D42"].number_format = '0%'
    ws["B42"].number_format = '#,##0'
    ws["C42"].number_format = '#,##0'

    # --- Column widths ---
    col_widths = {"A": 13.0, "B": 13.0, "C": 13.0, "D": 13.0,
                  "E": 13.0, "F": 13.0, "G": 13.0, "H": 13.0,
                  "I": 13.0, "J": 13.0, "K": 13.0, "L": 13.0, "M": 13.0}
    for cl, w in col_widths.items():
        ws.column_dimensions[cl].width = w

    # Row heights
    ws.row_dimensions[23].height = 39.6
    ws.row_dimensions[29].height = 27.6


def _set_header_cell(cell, text: str, wrap: bool = False):
    """Apply dark-blue header style to a cell."""
    cell.value = text
    cell.font = Font(name="等线", size=10, bold=True, color="FFFFFFFF")
    cell.fill = DARK_BLUE_FILL
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=wrap)
    _apply_border(cell)


def _apply_border(cell):
    """Apply thin border to a cell."""
    cell.border = THIN_BORDER


# ---- Task 3: Database query functions ----

def get_latest_date(cursor) -> str | None:
    """Find the latest date across all daily tables."""
    cursor.execute("""
        SELECT MAX(d) FROM (
            SELECT MAX(日期) AS d FROM Xiangwang.shop_daily_key_data
            UNION SELECT MAX(日期) FROM Xiangwang.shop_data_daily_registration
            UNION SELECT MAX(date_time) FROM Xiangwang.customer_service_performance_summary
        ) t
    """)
    row = cursor.fetchone()
    return str(row[0]) if row and row[0] else None


def get_shop_metric_today(cursor, table: str, column: str, date_col: str, biz_date: str) -> float:
    """Get a single metric value for a given date."""
    cursor.execute(
        f"SELECT COALESCE(`{column}`, 0) FROM Xiangwang.`{table}` WHERE `{date_col}` = %s",
        (biz_date,),
    )
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] else 0.0


def get_shop_metric_sum(cursor, table: str, column: str, date_col: str, biz_date: str) -> float:
    """Get SUM of a column for a given date (for multi-row tables like customer_service)."""
    cursor.execute(
        f"SELECT COALESCE(SUM(`{column}`), 0) FROM Xiangwang.`{table}` WHERE `{date_col}` = %s",
        (biz_date,),
    )
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] else 0.0


def get_alimama_sum(cursor, column: str, biz_date: str) -> float:
    """Sum a column across the 4 alimama channel tables for a given date."""
    tables = ["star_store", "tmall_express", "gravity_rubiks_cube", "wanxiangtai"]
    total = 0.0
    for tbl in tables:
        cursor.execute(
            f"SELECT `{column}` FROM Xiangwang.`{tbl}` WHERE date_time = %s",
            (biz_date,),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            total += parse_money(row[0])
    return total


def _write_pct_cell(cell, value: float | None):
    """Write a percentage cell with +/- sign and green/red color.

    Stores (value - 1) so format '+0.00%;-0.00%' renders e.g. '+6.84%' or '-27.53%'.
    """
    cell.number_format = '+0.00%;-0.00%'
    if value is None:
        cell.value = None
        cell.font = BLACK_FONT
    else:
        delta = value - 1.0
        cell.value = delta
        if delta > 0:
            cell.font = Font(name="等线", size=11, color="FF008000")
        elif delta < 0:
            cell.font = Font(name="等线", size=11, color="FFFF0000")
        else:
            cell.font = Font(name="等线", size=11, color="FF000000")
    cell.alignment = Alignment(vertical="center")
    _apply_border(cell)


def fill_shop_data_section(ws, cursor, biz_date: str):
    """Fill Rows 5-6 (VS Yesterday / VS LW) for B-G columns."""
    yesterday = str(date.fromisoformat(biz_date) - timedelta(days=1))
    lw_date = str(date.fromisoformat(biz_date) - timedelta(days=7))

    uv_today = get_shop_metric_today(cursor, "shop_data_daily_registration", "UV", "日期", biz_date)
    uv_yest = get_shop_metric_today(cursor, "shop_data_daily_registration", "UV", "日期", yesterday)
    uv_lw = get_shop_metric_today(cursor, "shop_data_daily_registration", "UV", "日期", lw_date)

    paid_uv_today = get_shop_metric_today(cursor, "shop_data_daily_registration", "PaidUV", "日期", biz_date)
    paid_uv_yest = get_shop_metric_today(cursor, "shop_data_daily_registration", "PaidUV", "日期", yesterday)
    paid_uv_lw = get_shop_metric_today(cursor, "shop_data_daily_registration", "PaidUV", "日期", lw_date)

    cost_today = get_shop_metric_today(cursor, "shop_daily_key_data", "cost_total", "日期", biz_date)
    cost_yest = get_shop_metric_today(cursor, "shop_daily_key_data", "cost_total", "日期", yesterday)
    cost_lw = get_shop_metric_today(cursor, "shop_daily_key_data", "cost_total", "日期", lw_date)

    bk_today = get_shop_metric_today(cursor, "shop_daily_key_data", "total_bookings", "日期", biz_date)
    bk_yest = get_shop_metric_today(cursor, "shop_daily_key_data", "total_bookings", "日期", yesterday)
    bk_lw = get_shop_metric_today(cursor, "shop_daily_key_data", "total_bookings", "日期", lw_date)

    paid_bk_today = get_alimama_sum(cursor, "order_count", biz_date)
    paid_bk_yest = get_alimama_sum(cursor, "order_count", yesterday)
    paid_bk_lw = get_alimama_sum(cursor, "order_count", lw_date)

    sales_today = get_alimama_sum(cursor, "sales", biz_date)
    sales_yest = get_alimama_sum(cursor, "sales", yesterday)
    sales_lw = get_alimama_sum(cursor, "sales", lw_date)
    roi_today = sales_today / cost_today if cost_today else 0
    roi_yest = sales_yest / cost_yest if cost_yest else 0
    roi_lw = sales_lw / cost_lw if cost_lw else 0

    metrics = [
        (2, uv_today, uv_yest, uv_lw),
        (3, paid_uv_today, paid_uv_yest, paid_uv_lw),
        (4, cost_today, cost_yest, cost_lw),
        (5, bk_today, bk_yest, bk_lw),
        (6, paid_bk_today, paid_bk_yest, paid_bk_lw),
        (7, roi_today, roi_yest, roi_lw),
    ]

    for col, today_val, yest_val, lw_val in metrics:
        vs_yest = today_val / yest_val if yest_val else None
        vs_lw = today_val / lw_val if lw_val else None
        _write_pct_cell(ws.cell(row=5, column=col), vs_yest)
        _write_pct_cell(ws.cell(row=6, column=col), vs_lw)


# ---- Task 4: CS data + monthly actual + MTD/YTD ----

def fill_cs_data_section(ws, cursor, biz_date: str):
    """Fill Rows 9-10 (VS Yesterday / VS LW) for 客服数据 B,C,F columns. D,E left empty for Phase 2."""
    yesterday = str(date.fromisoformat(biz_date) - timedelta(days=1))
    lw_date = str(date.fromisoformat(biz_date) - timedelta(days=7))

    zx_today = get_shop_metric_today(cursor, "shop_data_daily_registration", "咨询人数", "日期", biz_date)
    zx_yest = get_shop_metric_today(cursor, "shop_data_daily_registration", "咨询人数", "日期", yesterday)
    zx_lw = get_shop_metric_today(cursor, "shop_data_daily_registration", "咨询人数", "日期", lw_date)

    jd_today = get_shop_metric_sum(cursor, "customer_service_performance_summary", "接待人数", "date_time", biz_date)
    jd_yest = get_shop_metric_sum(cursor, "customer_service_performance_summary", "接待人数", "date_time", yesterday)
    jd_lw = get_shop_metric_sum(cursor, "customer_service_performance_summary", "接待人数", "date_time", lw_date)

    ord_today = get_shop_metric_sum(cursor, "customer_service_performance_summary", "订单数", "date_time", biz_date)
    ord_yest = get_shop_metric_sum(cursor, "customer_service_performance_summary", "订单数", "date_time", yesterday)
    ord_lw = get_shop_metric_sum(cursor, "customer_service_performance_summary", "订单数", "date_time", lw_date)

    cs_metrics = [
        (2, zx_today, zx_yest, zx_lw),
        (3, jd_today, jd_yest, jd_lw),
        (6, ord_today, ord_yest, ord_lw),
    ]

    for col, today_val, yest_val, lw_val in cs_metrics:
        vs_yest = today_val / yest_val if yest_val else None
        vs_lw = today_val / lw_val if lw_val else None
        _write_pct_cell(ws.cell(row=9, column=col), vs_yest)
        _write_pct_cell(ws.cell(row=10, column=col), vs_lw)

    # Columns D-E: 首响/平响 from team_dashboard_daily
    first_today = _get_team_dashboard_metric(cursor, "first_response_sec", biz_date)
    first_yest = _get_team_dashboard_metric(cursor, "first_response_sec", yesterday)
    first_lw = _get_team_dashboard_metric(cursor, "first_response_sec", lw_date)

    avg_today = _get_team_dashboard_metric(cursor, "avg_response_sec", biz_date)
    avg_yest = _get_team_dashboard_metric(cursor, "avg_response_sec", yesterday)
    avg_lw = _get_team_dashboard_metric(cursor, "avg_response_sec", lw_date)

    resp_metrics = [
        (4, first_today, first_yest, first_lw),  # D: 首响
        (5, avg_today, avg_yest, avg_lw),          # E: 平响
    ]
    for col, today_val, yest_val, lw_val in resp_metrics:
        vs_yest = today_val / yest_val if (today_val and yest_val) else None
        vs_lw = today_val / lw_val if (today_val and lw_val) else None
        _write_pct_cell(ws.cell(row=9, column=col), vs_yest)
        _write_pct_cell(ws.cell(row=10, column=col), vs_lw)


def _get_team_dashboard_metric(cursor, column: str, biz_date: str) -> float | None:
    """Get a metric from team_dashboard_daily. Returns None if no data."""
    cursor.execute(
        f"SELECT `{column}` FROM Xiangwang.team_dashboard_daily WHERE date_time = %s",
        (biz_date,),
    )
    row = cursor.fetchone()
    if row and row[0]:
        val = float(row[0])
        return val if val > 0 else None
    return None


def _write_response_pct_cell(cell, value: float | None):
    """Write a percentage cell for response time with +/- sign.

    Uses same color rule as _write_pct_cell: positive=green, negative=red, zero=black.
    Stores delta from 1.0, uses '+0.00%;-0.00%' format.
    """
    cell.number_format = '+0.00%;-0.00%'
    if value is None:
        cell.value = None
        cell.font = BLACK_FONT
    else:
        delta = value - 1.0
        cell.value = delta
        if delta > 0:
            cell.font = Font(name="等线", size=11, color="FF008000")  # up=green
        elif delta < 0:
            cell.font = Font(name="等线", size=11, color="FFFF0000")  # down=red
        else:
            cell.font = Font(name="等线", size=11, color="FF000000")  # flat=black
    cell.alignment = Alignment(vertical="center")
    _apply_border(cell)


def fill_monthly_actual_rows(ws, cursor, year: int):
    """Fill Row 25 (实际消耗) and Row 26 (转化单量) from alimama monthly aggregation."""
    tables = ["star_store", "tmall_express", "gravity_rubiks_cube", "wanxiangtai"]
    month_cols = list("BCDEFGHIJKLM")
    fiscal_bounds = get_fiscal_month_bounds(year)

    for i, col_letter in enumerate(month_cols):
        m_start, m_end = fiscal_bounds[i]

        total_cost = 0.0
        total_orders = 0.0
        for tbl in tables:
            cursor.execute(
                f"SELECT `cost`, `order_count` FROM Xiangwang.`{tbl}` "
                f"WHERE date_time >= %s AND date_time < %s",
                (m_start, m_end),
            )
            for row in cursor.fetchall():
                if row:
                    total_cost += parse_money(row[0])
                    total_orders += float(row[1] if row[1] else 0)

        ws[f"{col_letter}25"] = total_cost if total_cost else None
        ws[f"{col_letter}26"] = int(total_orders) if total_orders else None


# SKU keywords to exclude per SOP
# 补差/补、尾款、升/升级/升房/升舱、税费/补税、
# 改/改期/改航线、加人/加、生日礼遇、通兑
_PAX_EXCLUDE_KEYWORDS = [
    "补差", "补", "尾款",
    "升级", "升", "升房", "升舱",
    "税费", "补税",
    "改期", "改", "改航线",
    "加人", "加",
    "生日礼遇", "通兑",
]
# SOP 要求排除的订单状态（NULL 状态不排除）
_PAX_EXCLUDE_STATUSES = ("交易关闭", "等待买家付款")
# 预编译 SQL 条件：避免 MySQL NOT IN 对 NULL 的陷阱
_PAX_STATUS_CONDITION = (
    "(status_text IS NULL OR "
    + " AND ".join(f"status_text != '{s}'" for s in _PAX_EXCLUDE_STATUSES)
    + ")"
)


def _get_step1_pax(cursor, year: int, as_of_date: str | None = None) -> dict[int, int]:
    """Query order_list for step 1 monthly PAX.

    Returns dict {1: jan_pax, ..., 12: dec_pax}.
    """
    result: dict[int, int] = {}
    conditions = " AND ".join(
        [f"(package_type IS NULL OR package_type NOT LIKE '%%%%{kw}%%%%')"
         for kw in _PAX_EXCLUDE_KEYWORDS]
    )
    natural_bounds = get_natural_month_bounds(year)
    for month_num in range(1, 13):
        m_start, m_end = natural_bounds[month_num - 1]

        # 截断当前月份：不统计晚于 as_of_date 的记录
        if as_of_date:
            cutoff = (date.fromisoformat(as_of_date) + timedelta(days=1)).isoformat()
            if cutoff < m_end:
                m_end = cutoff

        cursor.execute(
            f"SELECT COALESCE(SUM(buy_mount), 0) FROM Xiangwang.order_list "
            f"WHERE order_date >= %s AND order_date < %s "
            f"AND {_PAX_STATUS_CONDITION} "
            f"AND ({conditions})",
            (m_start, m_end),
        )
        row = cursor.fetchone()
        result[month_num] = int(row[0]) if row and row[0] else 0
    return result


def _get_step2_pax(cursor, year: int, as_of_date: str | None = None) -> dict[int, int]:
    """Query order_list_secondary for step 2 monthly PAX.

    PAX = SUM(buy_mount). SOP: I列的数量 = buy_mount (飞猪API的pcount / 购买数量).
    Dedup via uk_order_id. Exclude 商家已驳回.
    """
    result: dict[int, int] = {m: 0 for m in range(1, 13)}
    natural_bounds = get_natural_month_bounds(year)
    for month_num in range(1, 13):
        m_start, m_end = natural_bounds[month_num - 1]

        if as_of_date:
            cutoff = (date.fromisoformat(as_of_date) + timedelta(days=1)).isoformat()
            if cutoff < m_end:
                m_end = cutoff

        cursor.execute(
            "SELECT COALESCE(SUM(buy_mount), 0) FROM Xiangwang.order_list_secondary "
            "WHERE submit_time >= %s AND submit_time < %s "
            "AND (status_text IS NULL OR status_text != '商家已驳回')",
            (m_start, m_end),
        )
        row = cursor.fetchone()
        result[month_num] = int(row[0]) if row and row[0] else 0
    return result


def _print_pax_audit(cursor, step1: dict, step2: dict, as_of_date: str | None):
    """输出月度 PAX 审计信息到 stderr，供人工核对。"""
    import sys as _sys
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    _sys.stderr.write(f"\n{'='*60}\n")
    _sys.stderr.write(f"PAX 审计 (as_of={as_of_date or '全月'})\n")
    _sys.stderr.write(f"{'='*60}\n")
    _sys.stderr.write(f"{'月':<6} {'Step1':>8} {'Step2':>8} {'合计':>8}\n")
    _sys.stderr.write(f"{'-'*30}\n")
    total_s1 = 0
    total_s2 = 0
    for m in range(1, 13):
        s1 = step1.get(m, 0)
        s2 = step2.get(m, 0)
        total_s1 += s1
        total_s2 += s2
        _sys.stderr.write(f"{month_names[m-1]:<6} {s1:>8} {s2:>8} {s1+s2:>8}\n")
    _sys.stderr.write(f"{'-'*30}\n")
    _sys.stderr.write(f"{'总计':<6} {total_s1:>8} {total_s2:>8} {total_s1+total_s2:>8}\n")

    # Step2 异常检查
    cursor.execute(
        "SELECT COUNT(*) FROM Xiangwang.order_list_secondary "
        "WHERE pax IS NULL"
    )
    null_pax = cursor.fetchone()[0]
    if null_pax:
        _sys.stderr.write(f"\n⚠️  {null_pax} 条 order_list_secondary.pax IS NULL "
                          f"(房型人数未解析)\n")

    # Step2 驳回状态检查
    cursor.execute(
        "SELECT COUNT(*) FROM Xiangwang.order_list_secondary "
        "WHERE status_text = '商家已驳回'"
    )
    rejected = cursor.fetchone()[0]
    if rejected:
        _sys.stderr.write(f"⚠️  {rejected} 条 order_list_secondary 状态为'商家已驳回' "
                          f"(已被 Step2 PAX 排除)\n")
    _sys.stderr.write(f"{'='*60}\n\n")


def fill_yearly_pax_step1(ws, cursor, year: int, as_of_date: str | None = None):
    """Fill C30:C41 with step 1 + step 2 combined monthly PAX."""
    step1 = _get_step1_pax(cursor, year, as_of_date)
    step2 = _get_step2_pax(cursor, year, as_of_date)

    for month_num in range(1, 13):
        total_pax = step1.get(month_num, 0) + step2.get(month_num, 0)
        r = 30 + month_num - 1
        if total_pax > 0:
            ws.cell(row=r, column=3).value = total_pax
            ws.cell(row=r, column=3).font = NORMAL_FONT
            ws.cell(row=r, column=3).number_format = '#,##0'
            ws.cell(row=r, column=3).alignment = Alignment(vertical="center")
            _apply_border(ws.cell(row=r, column=3))

    # 月度审计输出
    _print_pax_audit(cursor, step1, step2, as_of_date)


def _fiscal_month_idx(biz_date_str: str, year: int) -> int:
    """Return 0-based fiscal month index for a given date."""
    d = date.fromisoformat(biz_date_str)
    for i, (start_str, end_str) in enumerate(get_fiscal_month_bounds(year)):
        start = date.fromisoformat(start_str)
        end = date.fromisoformat(end_str)
        if start <= d < end:
            return i
    return d.month - 1  # fallback to calendar month


def _natural_month_idx(biz_date_str: str) -> int:
    """Return 0-based natural (calendar) month index."""
    return date.fromisoformat(biz_date_str).month - 1


def fill_mtd_ytd_section(ws, cursor, biz_date: str, year: int):
    """Fill MTD (Row 13-16) and YTD (Row 18-19) with formulas."""
    natural_idx = _natural_month_idx(biz_date)
    fiscal_idx = _fiscal_month_idx(biz_date, year)
    cols = list("BCDEFGHIJKLM")

    # Row 13-14: natural month → PAX
    ws["B13"] = f"=C{30 + natural_idx}"
    ws["B13"].font = NORMAL_FONT
    ws["B13"].alignment = Alignment(vertical="center")

    ws["B14"] = f"=D{30 + natural_idx}"
    ws["B14"].font = NORMAL_FONT
    ws["B14"].number_format = '0%'
    ws["B14"].alignment = Alignment(vertical="center")

    # Row 15-16: fiscal month → alimama
    ws["B15"] = f"={cols[fiscal_idx]}25"
    ws["B15"].font = NORMAL_FONT
    ws["B15"].number_format = '#,##0'
    ws["B15"].alignment = Alignment(vertical="center")

    ws["B16"] = f"={cols[fiscal_idx]}26"
    ws["B16"].font = NORMAL_FONT
    ws["B16"].alignment = Alignment(vertical="center")

    ws["B18"] = "=C42"
    ws["B18"].font = NORMAL_FONT
    ws["B18"].number_format = '#,##0'
    ws["B18"].alignment = Alignment(vertical="center")

    ws["B19"] = "=D42"
    ws["B19"].font = NORMAL_FONT
    ws["B19"].number_format = '0%'
    ws["B19"].alignment = Alignment(vertical="center")

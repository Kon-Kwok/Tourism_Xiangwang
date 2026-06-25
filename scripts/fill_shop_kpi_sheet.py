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

# Fixed budget values (Row 24, columns B-M)
MONTHLY_BUDGET = [180000, 165000, 250000, 200000, 250000, 250000,
                  200000, 200000, 165000, 300000, 250000, 165000]

# 2026 Monthly targets (B30-B41) — fixed reference values
MONTHLY_TARGETS = [682, 529, 909, 793, 1057, 1110, 962, 996, 737, 1586, 805, 408]

# Fiscal month labels (Row 23): Jan(1/1-1/20) through Dec(11/21-12/30)
FISCAL_MONTH_LABELS = [
    "Jan\n1/1-1/20", "Feb\n1/21-2/20", "Mar\n2/21-3/20",
    "Apr\n3/21-4/20", "May\n4/21-5/20", "Jun\n5/21-6/20",
    "Jul\n6/21-7/20", "Aug\n7/21-8/20", "Sep\n8/21-9/20",
    "Oct\n9/21-10/20", "Nov\n10/21-11/20", "Dec\n11/21-12/30",
]

# Month short labels (Row 30-41)
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NUMERIC_TEXT_RE = re.compile(r"^[¥￥]?([+-]?[\d,]+(?:\.\d*)?)$")


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


def build_sheet_structure(ws):
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
    ws["A6"] = "VS LV"
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
    ws["A10"] = "VS LV"
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
    ws["B29"] = "2026\ntarget"
    ws["C29"] = "2026\nActual"
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

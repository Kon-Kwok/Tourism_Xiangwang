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

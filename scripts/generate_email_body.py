#!/usr/bin/env python3
"""从导出的 Excel 中提取「店铺关键数据完成情况」sheet 第1-19行，生成邮件正文。

用法:
    python3 scripts/generate_email_body.py exports/象往日报_2026年5-6月.xlsx

默认输出 HTML 表格（可在邮件客户端中直接粘贴）。加 --text 输出纯文本。
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl
from openpyxl.cell.cell import Cell

FOOTER = (
    "请查收皇家加勒比飞猪旗舰店全店数据（店铺基础数据、赤兔统计数据、阿里妈妈推广等）。"
    "本次日报数据均采用AI数据采集工具批量自动化生成和发送，如有偏差，"
    "请随时联系项目经理或邮箱：rcclapac@the-shineon.com，我们将第一时间修正系统，谢谢。"
)

# Columns per row section
COL_COUNTS = {1: 2, 2: 1, 3: 1, 4: 7, 5: 7, 6: 7, 7: 1, 8: 6, 9: 6, 10: 6,
              11: 1, 12: 1, 13: 2, 14: 2, 15: 2, 16: 2, 17: 1, 18: 2, 19: 2}

# Row sections for HTML table grouping
SECTION_ROWS = [(4, 6), (8, 10)]  # 店铺数据, 客服数据
DARK_BLUE = "#002060"
WHITE = "#FFFFFF"
GREEN = "#008000"
RED = "#FF0000"
BLACK = "#000000"


def _rgb_from_cell(cell: Cell) -> str | None:
    """Extract hex RGB from a cell's font color, if any."""
    try:
        color = cell.font.color
        if color is None:
            return None
        if color.rgb:
            rgb = str(color.rgb)
            if len(rgb) == 8:
                return f"#{rgb[2:]}"  # strip alpha
            return f"#{rgb}"
        if color.theme is not None:
            return None  # theme colors are unreliable in openpyxl
    except Exception:
        pass
    return None


def cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        if isinstance(value, float) and -1 < value < 1:
            return f"{value:+.2%}"
        if value == int(value):
            return f"{int(value):,}"
        return f"{value:,.2f}"
    return str(value)


def resolve_formula(ws, ref_str: str):
    """Resolve =CELL reference or =IFERROR/SUM formula to a concrete value."""
    try:
        if ref_str.startswith("="):
            ref_str = ref_str[1:]
        if ref_str.startswith("IFERROR("):
            inner = ref_str[len("IFERROR("):].rsplit(",", 1)[0]
            if "/" in inner:
                a, b = inner.split("/", 1)
                av = resolve_formula(ws, a)
                bv = resolve_formula(ws, b)
                if av is not None and bv:
                    return av / bv
            return None
        if ref_str.startswith("SUM("):
            inner = ref_str[len("SUM("):].rstrip(")")
            sr, er = inner.split(":")
            sc, sr_num = sr[0], int(sr[1:])
            ec, er_num = er[0], int(er[1:])
            total = 0
            for rr in range(sr_num, er_num + 1):
                for cc in range(ord(sc) - 64, ord(ec) - 64 + 1):
                    v = ws.cell(row=rr, column=cc).value
                    if isinstance(v, (int, float)):
                        total += v
            return total
        c = ws[ref_str]
        v = c.value
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return v
        if isinstance(v, str) and v.startswith("="):
            return resolve_formula(ws, v[1:])
        return None
    except Exception:
        return None


def _resolve_cell(ws, row: int, col: int) -> tuple[str, str | None]:
    """Resolve cell value and return (display_text, font_color_hex)."""
    cell = ws.cell(row=row, column=col)
    v = cell.value
    color = None

    if v is None:
        return "", None

    s = str(v)
    if s.startswith("=IFERROR") or s.startswith("=SUM") or (s.startswith("=") and row >= 13):
        resolved = resolve_formula(ws, s)
        if resolved is not None:
            is_rate = s.startswith("=IFERROR") or "完成率" in str(ws.cell(row=row, column=1).value or "")
            if is_rate:
                text = f"{resolved:.1%}"
            elif isinstance(resolved, float) and -1 < resolved < 1:
                text = f"{resolved:+.2%}"
            elif isinstance(resolved, float):
                text = f"{resolved:,.2f}" if resolved != int(resolved) else f"{int(resolved):,}"
            else:
                text = str(resolved)
            # Color: only for VS delta values (-1~1 excluding 0), not completion rates
            if not is_rate and isinstance(resolved, float) and -1 < resolved < 1 and resolved != 0:
                color = GREEN if resolved > 0 else RED
            return text, color
        else:
            return cell_text(v), None

    if isinstance(v, float) and -1 < v < 1:
        text = f"{v:+.2%}"
        color = GREEN if v > 0 else RED if v < 0 else BLACK
        return text, color

    return cell_text(v), None


def _td(text: str, color: str | None = None, bold: bool = False,
        bg: str | None = None, align: str = "center", colspan: int = 1) -> str:
    """Build a <td> element with inline styles."""
    styles = [
        "border:1px solid #d0d0d0",
        "padding:4px 8px",
        "font-family:'等线',Arial,'Microsoft YaHei',sans-serif",
        "font-size:12px",
        f"text-align:{align}",
        "white-space:nowrap",
    ]
    if bold or bg:
        styles.append(f"font-weight:bold")
    if color:
        styles.append(f"color:{color}")
    if bg:
        styles.append(f"background-color:{bg}")
    attr = f'colspan="{colspan}"' if colspan > 1 else ""
    return f'<td {attr} style="{"; ".join(styles)}">{text}</td>'


def _hdr_td(text: str, colspan: int = 1) -> str:
    """Build a dark-blue header cell."""
    return _td(text, color=WHITE, bold=True, bg=DARK_BLUE, colspan=colspan)


HTML_WRAPPER_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>店铺关键数据完成情况</title>
</head>
<body style="font-family:'等线',Arial,'Microsoft YaHei',sans-serif;font-size:12px;">
"""

HTML_WRAPPER_TAIL = """</body>
</html>"""


def extract_html(ws) -> str:
    """Generate HTML email body mirroring the KPI sheet."""
    lines = [HTML_WRAPPER_HEAD]

    # === Row 1: Date ===
    date_val = cell_text(ws.cell(row=1, column=2).value)
    lines.append(f'<p style="margin:0 0 8px 0;">'
                 f'<b>店铺关键数据完成情况</b>&nbsp;&nbsp;Date: {date_val}</p>')

    # === 店铺数据 (Rows 4-6) ===
    lines.append('<table style="border-collapse:collapse;margin-bottom:8px;">')
    # Header row
    hdr_cells = []
    for c in range(1, 8):
        hdr_cells.append(_hdr_td(cell_text(ws.cell(row=4, column=c).value)))
    lines.append(f'<tr>{"".join(hdr_cells)}</tr>')
    # VS Yesterday & VS LW
    for r in (5, 6):
        row_cells = []
        for c in range(1, 8):
            text, color = _resolve_cell(ws, r, c)
            bold = c == 1
            row_cells.append(_td(text, color=color, bold=bold, align="left" if c == 1 else "center"))
        lines.append(f'<tr>{"".join(row_cells)}</tr>')
    lines.append('</table>')

    # === 客服数据 (Rows 8-10) ===
    lines.append('<table style="border-collapse:collapse;margin-bottom:8px;">')
    hdr_cells = []
    for c in range(1, 7):
        hdr_cells.append(_hdr_td(cell_text(ws.cell(row=8, column=c).value)))
    lines.append(f'<tr>{"".join(hdr_cells)}</tr>')
    for r in (9, 10):
        row_cells = []
        for c in range(1, 7):
            text, color = _resolve_cell(ws, r, c)
            bold = c == 1
            row_cells.append(_td(text, color=color, bold=bold, align="left" if c == 1 else "center"))
        lines.append(f'<tr>{"".join(row_cells)}</tr>')
    lines.append('</table>')

    # === MTD / YTD (Rows 12-19) ===
    lines.append('<table style="border-collapse:collapse;margin-bottom:8px;">')
    lines.append(f'<tr>{_hdr_td("Month Target", colspan=2)}</tr>')
    for r in range(13, 20):
        label_text, _ = _resolve_cell(ws, r, 1)
        val_text, val_color = _resolve_cell(ws, r, 2)
        if not label_text:
            continue
        lines.append(f'<tr>'
                     f'{_td(label_text, bold=True, align="left")}'
                     f'{_td(val_text, color=val_color)}'
                     f'</tr>')
    lines.append('</table>')

    # Footer
    lines.append(f'<p style="color:#666;margin-top:16px;">{FOOTER}</p>')
    lines.append(HTML_WRAPPER_TAIL)

    return "\n".join(lines)


def extract_text(ws) -> str:
    """Generate plain-text email body (fallback)."""
    # Collect all rows
    all_rows = []
    for r in range(1, 20):
        ncols = COL_COUNTS.get(r, 7)
        row_vals = []
        for c in range(1, ncols + 1):
            text, _ = _resolve_cell(ws, r, c)
            row_vals.append(text)
        if all(x == "" for x in row_vals):
            all_rows.append(None)
        else:
            all_rows.append(row_vals)

    # Dynamic column widths
    max_cols = max(len(r) for r in all_rows if r is not None)
    col_widths = [0] * max_cols
    for row_vals in all_rows:
        if row_vals is None:
            continue
        for i, val in enumerate(row_vals):
            w = sum(2 if '一' <= ch <= '鿿' or '　' <= ch <= '〿'
                    or '＀' <= ch <= '￯' else 1 for ch in str(val))
            if w > col_widths[i]:
                col_widths[i] = w
    col_widths = [w + 2 for w in col_widths]

    lines = []
    for row_vals in all_rows:
        if row_vals is None:
            lines.append("")
            continue
        line = ""
        for i, val in enumerate(row_vals):
            s = str(val)
            w = sum(2 if '一' <= ch <= '鿿' or '　' <= ch <= '〿'
                    or '＀' <= ch <= '￯' else 1 for ch in s)
            pad = col_widths[i] - w
            if pad > 0:
                s += " " * pad
            line += s
        lines.append(line.rstrip())

    lines.append("")
    lines.append(FOOTER)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/generate_email_body.py <excel文件路径> [--text]")
        sys.exit(1)

    text_mode = "--text" in sys.argv
    xlsx_path = Path(sys.argv[1])
    if not xlsx_path.exists():
        print(f"错误: 文件不存在 - {xlsx_path}")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path)
    if "店铺关键数据完成情况" not in wb.sheetnames:
        print("错误: 未找到「店铺关键数据完成情况」sheet")
        sys.exit(1)

    ws = wb["店铺关键数据完成情况"]
    if text_mode:
        print(extract_text(ws))
    else:
        print(extract_html(ws))


if __name__ == "__main__":
    main()

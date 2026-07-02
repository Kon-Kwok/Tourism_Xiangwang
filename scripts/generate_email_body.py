#!/usr/bin/env python3
"""从导出的 Excel 中提取「店铺关键数据完成情况」sheet 第1-19行，生成邮件正文。

用法:
    python3 scripts/generate_email_body.py exports/象往日报_2026年5-6月.xlsx

输出可直接粘贴到邮件正文。
"""
from __future__ import annotations

import sys
from pathlib import Path

import openpyxl

FOOTER = (
    "请查收皇家加勒比飞猪旗舰店全店数据（店铺基础数据、赤兔统计数据、阿里妈妈推广等）。"
    "本次日报数据均采用AI数据采集工具批量自动化生成和发送，如有偏差，"
    "请随时联系项目经理或邮箱：rcclapac@the-shineon.com，我们将第一时间修正系统，谢谢。"
)

# Columns per row section
COL_COUNTS = {1: 2, 2: 1, 3: 1, 4: 7, 5: 7, 6: 7, 7: 1, 8: 6, 9: 6, 10: 6,
              11: 1, 12: 1, 13: 2, 14: 2, 15: 2, 16: 2, 17: 1, 18: 2, 19: 2}


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
        # =IFERROR(C35/B35,"")
        if ref_str.startswith("IFERROR("):
            inner = ref_str[len("IFERROR("):].rsplit(",", 1)[0]
            if "/" in inner:
                a, b = inner.split("/", 1)
                av = resolve_formula(ws, a)
                bv = resolve_formula(ws, b)
                if av is not None and bv:
                    return av / bv
            return None
        # =SUM(C30:C41)
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
        # =C35 or =H25
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


def extract(ws) -> str:
    lines = []
    for r in range(1, 20):
        ncols = COL_COUNTS.get(r, 7)
        row_vals = []
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            v = cell.value
            if v is None:
                row_vals.append("")
                continue
            s = str(v)
            if s.startswith("=IFERROR") or s.startswith("=SUM") or (s.startswith("=") and r >= 13):
                resolved = resolve_formula(ws, s)
                if resolved is not None:
                    # D列完成率是比值(如1.078), 非delta; Row9-10 VS是delta
                    is_rate = s.startswith("=IFERROR") or "完成率" in str(ws.cell(row=r, column=1).value or "")
                    if is_rate:
                        row_vals.append(f"{resolved:.1%}")
                    elif isinstance(resolved, float) and -1 < resolved < 1:
                        row_vals.append(f"{resolved:+.2%}")
                    elif isinstance(resolved, float):
                        row_vals.append(f"{resolved:,.2f}" if resolved != int(resolved) else f"{int(resolved):,}")
                    else:
                        row_vals.append(str(resolved))
                else:
                    row_vals.append(cell_text(v))
            elif isinstance(v, float) and -1 < v < 1:
                row_vals.append(f"{v:+.2%}")
            else:
                row_vals.append(cell_text(v))

        # Skip completely empty rows
        if all(x == "" for x in row_vals):
            continue

        # Align columns
        line = ""
        for i, val in enumerate(row_vals):
            width = 14 if i > 0 else 18
            line += str(val).ljust(width)
        lines.append(line.rstrip())

    lines.append("")
    lines.append(FOOTER)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/generate_email_body.py <excel文件路径>")
        sys.exit(1)

    xlsx_path = Path(sys.argv[1])
    if not xlsx_path.exists():
        print(f"错误: 文件不存在 - {xlsx_path}")
        sys.exit(1)

    wb = openpyxl.load_workbook(xlsx_path)
    if "店铺关键数据完成情况" not in wb.sheetnames:
        print("错误: 未找到「店铺关键数据完成情况」sheet")
        sys.exit(1)

    ws = wb["店铺关键数据完成情况"]
    print(extract(ws))


if __name__ == "__main__":
    main()

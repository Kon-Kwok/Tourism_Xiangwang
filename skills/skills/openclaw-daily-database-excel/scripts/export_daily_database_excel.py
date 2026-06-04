#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterable

import openpyxl
import pymysql
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


PROJECT_ROOT = Path(__file__).resolve().parents[5]
DEFAULT_TABLES = (
    ("customer_service_data_daily", "日期", "赤兔-人均日接入"),
    ("customer_service_performance_summary", "date_time", "赤兔-每周店铺个人数据"),
    ("customer_service_performance_workload_analysis", "date_time", "赤兔-客服数据23年新"),
    ("shop_daily_key_data", "日期", "店铺日度关键数据"),
    ("shop_data_daily_registration", "日期", "店铺每日登记"),
    ("star_store", "date_time", "阿里妈妈-明星店铺"),
    ("tmall_express", "date_time", "阿里妈妈-直通车"),
    ("gravity_rubiks_cube", "date_time", "阿里妈妈-引力魔方"),
    ("wanxiangtai", "date_time", "阿里妈妈-万相台"),
    ("wanxiangtai_2", "date_time", "阿里妈妈-万相台2"),
)
TABLE_DISPLAY_NAMES = {table_name: display_name for table_name, _, display_name in DEFAULT_TABLES}
DATE_COLUMN_CANDIDATES = ("日期", "date_time", "order_date", "biz_date", "collection_date")
EXCLUDE_COLUMNS = {"created_at", "updated_at"}
ALIMAMA_CHANNELS = ("明星店铺", "直通车", "引力魔方", "万相台")
ALIMAMA_TABLE_MAP = {
    "明星店铺": "star_store",
    "直通车": "tmall_express",
    "引力魔方": "gravity_rubiks_cube",
    "万相台": "wanxiangtai",
}
ALIMAMA_BASE_METRICS = ("cost", "imp", "click", "order", "sales", "shopping_cart", "bookmark_product", "bookmark_store")
NUMERIC_TEXT_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
HEADER_FILL = "FF305496"
HEADER_FONT_COLOR = "FFF2F2F2"
BODY_FONT_COLOR = "FF000000"
BORDER_COLOR = "FFB7C3D0"
DEFAULT_FONT = "等线"

SHEET_COLUMN_EXCLUSIONS: dict[str, set[str]] = {
    "店铺每日登记": {"id"},
    "阿里妈妈-明星店铺": {"id", "cart_rate"},
    "阿里妈妈-直通车": {"id", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"},
    "阿里妈妈-引力魔方": {"id", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"},
    "阿里妈妈-万相台": {"id", "bookmark_store", "collection_cart_cost", "collection_cart_count", "collection_cart_rate"},
}

SHEET_DATE_REFORMAT: dict[str, str] = {
    "赤兔-人均日接入": "日期",
    "赤兔-每周店铺个人数据": "date_time",
    "赤兔-客服数据23年新": "date_time",
    "店铺每日登记": "日期",
    "阿里妈妈-明星店铺": "date_time",
    "阿里妈妈-直通车": "date_time",
    "阿里妈妈-引力魔方": "date_time",
    "阿里妈妈-万相台": "date_time",
}

SHEET_DATE_TO_END: set[str] = {
    "赤兔-每周店铺个人数据",
    "赤兔-客服数据23年新",
}

SHEET_COLUMN_WIDTHS: dict[str, dict[str, float]] = {
    "赤兔-人均日接入": {
        "询单最终付款成功率": 27.52,
        "__default__": 13.42,
    },
}

SHEET_CURRENCY_COLUMNS: dict[str, set[str]] = {
    "阿里妈妈-明星店铺": {"cost", "cpc"},
    "阿里妈妈-直通车": {"cost", "cpc"},
    "阿里妈妈-引力魔方": {"cost", "cpm", "roi"},
    "阿里妈妈-万相台": {"cost"},
}

SHEET_DECIMAL_FORMATS: dict[str, dict[str, str]] = {
    "阿里妈妈-明星店铺": {"roi": "0.00"},
}


def load_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_date(value: str | None) -> str:
    if value is None:
        return date.today().isoformat()
    return datetime.strptime(value, "%Y-%m-%d").date().isoformat()


def connect(args):
    return pymysql.connect(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        charset="utf8mb4",
        connect_timeout=5,
    )


def existing_default_tables(cursor, database: str) -> list[tuple[str, str, str]]:
    available = []
    for table_name, date_column, display_name in DEFAULT_TABLES:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
            """,
            (database, table_name, date_column),
        )
        if cursor.fetchone()[0]:
            available.append((table_name, date_column, display_name))
    return available


def all_date_tables(cursor, database: str) -> list[tuple[str, str, str]]:
    placeholders = ", ".join(["%s"] * len(DATE_COLUMN_CANDIDATES))
    cursor.execute(
        f"""
        SELECT TABLE_NAME, COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND COLUMN_NAME IN ({placeholders})
        ORDER BY TABLE_NAME,
          FIELD(COLUMN_NAME, {placeholders})
        """,
        (database, *DATE_COLUMN_CANDIDATES, *DATE_COLUMN_CANDIDATES),
    )
    seen = set()
    tables = []
    for table_name, column_name in cursor.fetchall():
        if table_name in seen:
            continue
        seen.add(table_name)
        tables.append((table_name, column_name, TABLE_DISPLAY_NAMES.get(table_name, table_name)))
    return tables


def _clean_columns_rows(columns, rows, date_column, sheet_name=None):
    extra_exclude = SHEET_COLUMN_EXCLUSIONS.get(sheet_name, set())
    keep_idx = [i for i, col in enumerate(columns) if col not in EXCLUDE_COLUMNS and col not in extra_exclude]
    columns = [columns[i] for i in keep_idx]
    rows = [tuple(row[i] for i in keep_idx) for row in rows]
    move_date_to_end = sheet_name in SHEET_DATE_TO_END
    new_order = []
    for head in ("id", date_column):
        if not move_date_to_end or head != date_column:
            try:
                idx = columns.index(head)
                new_order.append(idx)
            except ValueError:
                pass
    for i in range(len(columns)):
        if i not in new_order:
            new_order.append(i)
    if move_date_to_end:
        try:
            idx = columns.index(date_column)
            new_order.remove(idx)
            new_order.append(idx)
        except ValueError:
            pass
    columns = [columns[i] for i in new_order]
    rows = [tuple(row[i] for i in new_order) for row in rows]
    return columns, rows


def fetch_table(cursor, database: str, table_name: str, date_column: str, biz_date: str, sheet_name=None):
    cursor.execute(f"SELECT * FROM `{database}`.`{table_name}` WHERE `{date_column}` = %s", (biz_date,))
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    return _clean_columns_rows(columns, rows, date_column, sheet_name)


def fetch_table_range(cursor, database: str, table_name: str, date_column: str, start_date: str, end_date: str, sheet_name=None):
    cursor.execute(
        f"SELECT * FROM `{database}`.`{table_name}` WHERE `{date_column}` BETWEEN %s AND %s ORDER BY `{date_column}`, `id`",
        (start_date, end_date),
    )
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    return _clean_columns_rows(columns, rows, date_column, sheet_name)


def safe_sheet_name(name: str, used: set[str]) -> str:
    base = name[:31]
    candidate = base
    index = 2
    while candidate in used:
        suffix = f"_{index}"
        candidate = f"{base[:31 - len(suffix)]}{suffix}"
        index += 1
    used.add(candidate)
    return candidate


def _convert_numeric_text(value):
    if value is None or isinstance(value, bool):
        return value, None
    if isinstance(value, Decimal):
        return float(value), None
    if isinstance(value, (int, float)):
        return value, None
    if not isinstance(value, str):
        return value, None

    text = value.strip()
    if not text:
        return value, None

    is_percent = text.endswith("%")
    if is_percent:
        text = text[:-1].strip()

    text = text.replace(",", "").replace("，", "")
    text = text.replace("￥", "").replace("¥", "").strip()
    if not NUMERIC_TEXT_RE.match(text):
        return value, None

    number = float(text)
    if is_percent:
        return number / 100, "0.00%"
    if number.is_integer() and "." not in text:
        return int(number), None
    return number, None


def write_sheet(workbook, sheet_name: str, columns: Iterable[str], rows: Iterable[tuple], used: set[str]) -> int:
    worksheet = workbook.create_sheet(safe_sheet_name(sheet_name, used))
    worksheet.append(list(columns))
    count = 0
    for row in rows:
        converted_row = []
        number_formats = []
        for value in row:
            converted_value, number_format = _convert_numeric_text(value)
            converted_row.append(converted_value)
            number_formats.append(number_format)
        worksheet.append(converted_row)
        for cell, number_format in zip(worksheet[worksheet.max_row], number_formats):
            if number_format is not None:
                cell.number_format = number_format
        count += 1
    worksheet.freeze_panes = "A2"
    return count


COLUMN_FORMAT_RULES: dict[str, dict[str, str]] = {
    "赤兔-人均日接入": {
        "回复率": "0.00%",
        "询单最终付款成功率": "0.00%",
        "评价发送率": "0.00%",
        "客户满意比": "0.0000",
        "很满意": "0",
        "满意": "0",
        "一般": "0",
        "不满意": "0",
        "很不满意": "0",
    },
    "赤兔-每周店铺个人数据": {
        "询单人数": "0",
    },
    "赤兔-客服数据23年新": {
        "未回复人数": "0.00%",
        "旺旺回复率": "0.00%",
    },
    "店铺每日登记": {
        "咨询转化率": "0.00%",
        "下单转化率": "0.00%",
    },
}


def _apply_cell_formats(workbook) -> None:
    for worksheet in workbook.worksheets:
        name = worksheet.title
        rules = COLUMN_FORMAT_RULES.get(name)
        if rules is None:
            continue

        header_row = worksheet[1]
        col_indices: dict[str, int] = {}
        for idx, cell in enumerate(header_row):
            if cell.value in rules:
                col_indices[cell.value] = idx

        if not col_indices:
            continue

        for row in worksheet.iter_rows(min_row=2):
            for col_name, col_idx in col_indices.items():
                cell = row[col_idx]
                fmt_code = rules[col_name]
                value = cell.value

                if value is None:
                    continue

                if isinstance(value, str):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        continue

                cell.value = value
                cell.number_format = fmt_code


def _handle_delay_chat_volume(workbook, summary: list) -> None:
    """替换最新日期的 chat_volume=0 为 '延迟统计'。"""
    ws = None
    for worksheet in workbook.worksheets:
        if worksheet.title == "店铺日度关键数据":
            ws = worksheet
            break
    if ws is None:
        return

    header_row = ws[1]
    date_col_idx, chat_col_idx = None, None
    for idx, cell in enumerate(header_row):
        if cell.value == "日期":
            date_col_idx = idx
        elif cell.value == "chat_volume":
            chat_col_idx = idx
    if date_col_idx is None or chat_col_idx is None:
        return

    dates = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        d = row[date_col_idx]
        if isinstance(d, date):
            dates.add(d)
    max_date = max(dates) if dates else None

    if max_date is None:
        return

    for row in ws.iter_rows(min_row=2):
        date_cell = row[date_col_idx]
        chat_cell = row[chat_col_idx]
        if isinstance(date_cell.value, date) and date_cell.value == max_date and chat_cell.value == 0:
            chat_cell.value = "延迟统计"
            chat_cell.number_format = "@"


DELAY_COLUMNS: dict[str, set[str]] = {
    "赤兔-人均日接入": {
        "询单最终付款成功率",
        "评价发送率",
        "客户满意比",
        "很满意",
        "满意",
        "一般",
        "不满意",
        "很不满意",
    },
    "赤兔-每周店铺个人数据": {
        "询单人数",
    },
}


def _handle_delay_kpi_fields(workbook) -> None:
    for worksheet in workbook.worksheets:
        delay_cols = DELAY_COLUMNS.get(worksheet.title)
        if not delay_cols:
            continue
        header_row = worksheet[1]
        col_indices: dict[str, int] = {}
        for idx, cell in enumerate(header_row):
            if cell.value in delay_cols:
                col_indices[cell.value] = idx
        if not col_indices:
            continue
        for row in worksheet.iter_rows(min_row=2):
            for col_name, col_idx in col_indices.items():
                cell = row[col_idx]
                if cell.value is None:
                    cell.value = "延迟统计"
                    cell.number_format = "@"


def _apply_date_reformat(workbook) -> None:
    """Convert date columns from yyyy-mm-dd to yyyy/mm/dd format."""
    from datetime import datetime as dt_type
    for worksheet in workbook.worksheets:
        date_col_name = SHEET_DATE_REFORMAT.get(worksheet.title)
        if not date_col_name:
            continue
        header_row = worksheet[1]
        col_idx = None
        for idx, cell in enumerate(header_row):
            if cell.value == date_col_name:
                col_idx = idx
                break
        if col_idx is None:
            continue
        for row in worksheet.iter_rows(min_row=2):
            cell = row[col_idx]
            if cell.value is not None:
                if isinstance(cell.value, (date, dt_type)):
                    cell.number_format = "YYYY/MM/DD"
                elif isinstance(cell.value, str):
                    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
                        try:
                            parsed = dt_type.strptime(cell.value, fmt)
                            cell.value = parsed
                            cell.number_format = "YYYY/MM/DD"
                            break
                        except ValueError:
                            continue


def _apply_currency_separator_formats(workbook) -> None:
    """Apply currency format and thousand separator to designated columns."""
    for worksheet in workbook.worksheets:
        name = worksheet.title
        currency_cols = SHEET_CURRENCY_COLUMNS.get(name, set())
        decimal_fmts = SHEET_DECIMAL_FORMATS.get(name, {})
        if not currency_cols and not decimal_fmts:
            continue
        header_row = worksheet[1]
        col_map: dict[str, int] = {}
        for idx, cell in enumerate(header_row):
            col_map[cell.value] = idx

        for row in worksheet.iter_rows(min_row=2):
            for col_name in currency_cols:
                if col_name not in col_map:
                    continue
                cell = row[col_map[col_name]]
                if cell.value is not None:
                    val = cell.value
                    if isinstance(val, (int, float)):
                        cell.number_format = '￥#,##0.00'
                    elif isinstance(val, str):
                        try:
                            cleaned = val.replace(",", "").replace("，", "").replace("￥", "").replace("¥", "").strip()
                            cell.value = float(cleaned)
                            cell.number_format = '￥#,##0.00'
                        except (ValueError, TypeError):
                            pass
            for col_name, fmt in decimal_fmts.items():
                if col_name not in col_map:
                    continue
                cell = row[col_map[col_name]]
                if cell.value is not None:
                    cell.number_format = fmt


def _apply_shop_daily_reg_thousand_sep(workbook) -> None:
    """Apply thousand separator to B-G columns of 店铺每日登记."""
    for worksheet in workbook.worksheets:
        if worksheet.title != "店铺每日登记":
            continue
        for row in worksheet.iter_rows(min_row=2):
            for col_idx in range(1, 7):
                if col_idx >= len(row):
                    continue
                cell = row[col_idx]
                if cell.value is not None and isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0'


def _apply_sheet_column_widths(workbook) -> None:
    """Override column widths for sheets with specific width rules."""
    for worksheet in workbook.worksheets:
        rules = SHEET_COLUMN_WIDTHS.get(worksheet.title)
        if not rules:
            continue
        default_width = rules.get("__default__")
        header_row = worksheet[1]
        for idx, cell in enumerate(header_row):
            col_letter = worksheet.cell(1, idx + 1).column_letter
            col_name = cell.value
            if col_name in rules:
                worksheet.column_dimensions[col_letter].width = rules[col_name]
            elif default_width is not None:
                worksheet.column_dimensions[col_letter].width = default_width


def _monthly_period_for_date(ref_date: date) -> tuple[date, date, str]:
    if ref_date.month == 1 and ref_date.day <= 20:
        start, end, label = date(ref_date.year, 1, 1), date(ref_date.year, 1, 20), f"{ref_date.year}年1月"
    elif ref_date.day <= 20:
        start = date(ref_date.year, ref_date.month - 1, 21)
        end = date(ref_date.year, ref_date.month, 20)
        label = f"{start.month}月{start.day}号-{end.month}月{end.day}号"
    elif ref_date.month == 12:
        start, end, label = date(ref_date.year, 11, 21), date(ref_date.year, 12, 31), "11月21号-12月31号"
    else:
        start = date(ref_date.year, ref_date.month, 21)
        end = date(ref_date.year, ref_date.month + 1, 20)
        label = f"{start.month}月{start.day}号-{end.month}月{end.day}号"
    return start, end, label


def _previous_period(start: date) -> tuple[date, date, str]:
    prev_end = start - timedelta(days=1)
    if start == date(start.year, 1, 1):
        return date(start.year - 1, 11, 21), date(start.year - 1, 12, 31), "11月21号-12月31号"
    if start.day == 21:
        return date(start.year, start.month - 1, 21), date(start.year, start.month, 20), f"{start.month - 1}月21号-{start.month}月20号"
    return date(start.year, start.month - 1, 21), date(start.year, start.month, 20), f"{start.month - 1}月21号-{start.month}月20号"


def _parse_alimama_number(value) -> float:
    if value is None or isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    if not isinstance(value, str):
        return 0.0
    text = value.strip()
    if not text or text == "-":
        return 0.0
    text = text.replace(",", "").replace("，", "").replace("￥", "").replace("¥", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _fetch_alimama_aggregate(cursor, database: str, channel_tables: list[str], start: date, end: date) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for channel, table in ALIMAMA_TABLE_MAP.items():
        cursor.execute(
            f"SELECT date_time, cost, imp, click, order_count, sales, shopping_cart, bookmark_product, bookmark_store "
            f"FROM `{database}`.`{table}` WHERE date_time BETWEEN %s AND %s",
            (start.isoformat(), end.isoformat()),
        )
        totals = {key: 0.0 for key in ALIMAMA_BASE_METRICS}
        total_bookmark = 0.0
        for row in cursor.fetchall():
            totals["cost"] += _parse_alimama_number(row[1])
            totals["imp"] += _parse_alimama_number(row[2])
            totals["click"] += _parse_alimama_number(row[3])
            totals["order"] += _parse_alimama_number(row[4])
            totals["sales"] += _parse_alimama_number(row[5])
            totals["shopping_cart"] += _parse_alimama_number(row[6])
            totals["bookmark_product"] += _parse_alimama_number(row[7])
            totals["bookmark_store"] += _parse_alimama_number(row[8])
        totals["bookmark_total"] = totals["bookmark_product"] + totals["bookmark_store"]
        result[channel] = totals
    return result


def build_alimama_monthly_sheet(workbook, conn, args, biz_date_str: str, used_names: set[str]) -> None:
    biz_date = datetime.strptime(biz_date_str, "%Y-%m-%d").date()
    period_start, period_end, period_label = _monthly_period_for_date(biz_date)
    prev_start, prev_end, _ = _previous_period(period_start)

    with conn.cursor() as cursor:
        current_data = _fetch_alimama_aggregate(cursor, args.database, list(ALIMAMA_TABLE_MAP.values()), period_start, period_end)
        previous_data = _fetch_alimama_aggregate(cursor, args.database, list(ALIMAMA_TABLE_MAP.values()), prev_start, prev_end)

    sheet_name = safe_sheet_name("阿里妈妈月汇总", used_names)
    ws = workbook.create_sheet(sheet_name)

    headers = [
        "", "花费", "展示", "点击", "订单", "销量",
        "加入购物车", "宝贝收藏", "店铺收藏",
        "CTR", "CPC", "CPM", "ROI", "CVR",
        "ASP", "订单成本", "加购成本",
    ]
    ws.append(headers)

    def write_period_block(label: str, data: dict, prev_data: dict | None = None):
        ws.append([label] + [""] * (len(headers) - 1))
        block_start = ws.max_row + 1
        for channel in ALIMAMA_CHANNELS:
            d = data.get(channel, {})
            row_num = ws.max_row + 1
            cost = d.get("cost", 0)
            imp = d.get("imp", 0)
            click = d.get("click", 0)
            order = d.get("order", 0)
            sales = d.get("sales", 0)
            cart = d.get("shopping_cart", 0)
            bp = d.get("bookmark_product", 0)
            bs = d.get("bookmark_store", 0)
            ws.append([
                channel, cost, imp, click, order, sales,
                cart, bp, bs,
                f"=D{row_num}/C{row_num}",          # CTR
                f"=B{row_num}/D{row_num}",          # CPC
                f"=(B{row_num}/C{row_num})*1000",    # CPM
                f"=F{row_num}/B{row_num}",          # ROI
                f"=E{row_num}/D{row_num}",          # CVR
                f"=IF(E{row_num}=0,0,F{row_num}/E{row_num})",  # ASP
                f"=IF(E{row_num}=0,0,B{row_num}/E{row_num})",  # 订单成本
                f"=B{row_num}/G{row_num}",          # 加购成本
            ])

        total_row = ws.max_row + 1
        ws.append(["总计"] + [f"=SUM({chr(65+c)}{block_start}:{chr(65+c)}{total_row-1})" for c in range(1, 9)] + [""] * 8)
        ws.cell(total_row, 10).value = f"=D{total_row}/C{total_row}"  # CTR
        ws.cell(total_row, 11).value = f"=B{total_row}/D{total_row}"  # CPC
        ws.cell(total_row, 12).value = f"=(B{total_row}/C{total_row})*1000"  # CPM
        ws.cell(total_row, 13).value = f"=F{total_row}/B{total_row}"  # ROI
        ws.cell(total_row, 14).value = f"=E{total_row}/D{total_row}"  # CVR
        ws.cell(total_row, 15).value = f"=IF(E{total_row}=0,0,F{total_row}/E{total_row})"  # ASP
        ws.cell(total_row, 16).value = f"=IF(E{total_row}=0,0,B{total_row}/E{total_row})"  # 订单成本
        ws.cell(total_row, 17).value = f"=B{total_row}/G{total_row}"  # 加购成本

        return block_start, total_row

    write_period_block(period_label, current_data)
    _, prev_total = write_period_block(f"{prev_start.month}月{prev_start.day}号-{prev_end.month}月{prev_end.day}号", previous_data)

    # Hide the previous period rows
    for row in range(prev_total - len(ALIMAMA_CHANNELS) - 1, prev_total + 1):
        ws.row_dimensions[row].hidden = True

    ws.freeze_panes = "B3"


def autosize_workbook(workbook) -> None:
    for worksheet in workbook.worksheets:
        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells[:100]:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 10), 40)


def apply_standard_table_style(workbook) -> None:
    alignment = Alignment(horizontal="center", vertical="center")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_fill = PatternFill("solid", fgColor=HEADER_FILL)
    header_font = Font(name=DEFAULT_FONT, size=11, bold=True, color=HEADER_FONT_COLOR)
    body_font = Font(name=DEFAULT_FONT, size=11, color=BODY_FONT_COLOR)
    thin_side = Side(style="thin", color=BORDER_COLOR)
    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    for worksheet in workbook.worksheets:
        for row in worksheet.iter_rows():
            for cell in row:
                cell.border = thin_border
                cell.alignment = alignment
                cell.font = body_font
        if worksheet.max_row >= 1:
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment
            worksheet.row_dimensions[1].height = 41.4


def build_workbook(conn, args, biz_date: str, start_date: str = None, end_date: str = None):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    used_sheet_names: set[str] = set()
    summary = []
    range_mode = start_date is not None and end_date is not None

    with conn.cursor() as cursor:
        tables = all_date_tables(cursor, args.database) if args.all_date_tables else existing_default_tables(cursor, args.database)

        for table_name, date_column, display_name in tables:
            if range_mode:
                columns, rows = fetch_table_range(cursor, args.database, table_name, date_column, start_date, end_date, display_name)
            else:
                columns, rows = fetch_table(cursor, args.database, table_name, date_column, biz_date, display_name)
            row_count = write_sheet(workbook, display_name, columns, rows, used_sheet_names)
            summary.append((display_name, date_column, row_count))

    build_alimama_monthly_sheet(workbook, conn, args, biz_date or end_date, used_sheet_names)

    _apply_cell_formats(workbook)
    _apply_date_reformat(workbook)
    _apply_currency_separator_formats(workbook)
    _apply_shop_daily_reg_thousand_sep(workbook)
    _handle_delay_chat_volume(workbook, summary)
    _handle_delay_kpi_fields(workbook)
    autosize_workbook(workbook)
    _apply_sheet_column_widths(workbook)
    apply_standard_table_style(workbook)
    return workbook, summary


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser(description="Export Xiangwang daily database rows to Excel")
    parser.add_argument("--date", help="Business date, format YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--start", help="Start date for range export, format YYYY-MM-DD.")
    parser.add_argument("--end", help="End date for range export, format YYYY-MM-DD.")
    parser.add_argument("--output", help="Output xlsx path. Defaults to exports/daily_database_YYYY-MM-DD.xlsx")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3306")))
    parser.add_argument("--user", default=os.environ.get("USER", "remote_user"))
    parser.add_argument("--password", default=os.environ.get("PASS", "Tourism2024"))
    parser.add_argument("--database", default=os.environ.get("DATABASE", "Xiangwang"))
    parser.add_argument("--all-date-tables", action="store_true", help="Export every table with a recognized date column.")
    parser.add_argument("--include-empty-tables", action="store_true", help="Also create sheets for tables with no rows on the selected date.")
    args = parser.parse_args()

    range_mode = args.start is not None and args.end is not None
    if (args.start is not None) != (args.end is not None):
        parser.error("--start and --end must be used together")

    if range_mode:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
        biz_date = None
    else:
        biz_date = parse_date(args.date)
        start_date = end_date = None

    if args.output:
        output_path = Path(args.output)
    elif range_mode:
        output_path = PROJECT_ROOT / "exports" / f"daily_database_{start_date}_{end_date}.xlsx"
    else:
        output_path = PROJECT_ROOT / "exports" / f"daily_database_{biz_date}.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = connect(args)
    except pymysql.err.OperationalError:
        if "--host" in os.sys.argv or args.host in ("127.0.0.1", "localhost"):
            raise
        args.host = "127.0.0.1"
        conn = connect(args)
    try:
        workbook, summary = build_workbook(conn, args, biz_date=biz_date, start_date=start_date, end_date=end_date)
        workbook.save(output_path)
    finally:
        conn.close()

    print(f"output={output_path}")
    for table_name, date_column, row_count in summary:
        print(f"{table_name}\t{date_column}\t{row_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

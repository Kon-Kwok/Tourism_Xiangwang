#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import openpyxl
import pymysql


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
    ("order_list", "order_date", "飞猪订单明细"),
)
TABLE_DISPLAY_NAMES = {table_name: display_name for table_name, _, display_name in DEFAULT_TABLES}
DATE_COLUMN_CANDIDATES = ("日期", "date_time", "order_date", "biz_date", "collection_date")
EXCLUDE_COLUMNS = {"created_at", "updated_at"}


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


def fetch_table(cursor, database: str, table_name: str, date_column: str, biz_date: str):
    cursor.execute(f"SELECT * FROM `{database}`.`{table_name}` WHERE `{date_column}` = %s", (biz_date,))
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    keep_idx = [i for i, col in enumerate(columns) if col not in EXCLUDE_COLUMNS]
    columns = [columns[i] for i in keep_idx]
    rows = [tuple(row[i] for i in keep_idx) for row in rows]
    new_order = []
    for head in ("id", date_column):
        try:
            idx = columns.index(head)
            new_order.append(idx)
        except ValueError:
            pass
    for i in range(len(columns)):
        if i not in new_order:
            new_order.append(i)
    columns = [columns[i] for i in new_order]
    rows = [tuple(row[i] for i in new_order) for row in rows]
    return columns, rows


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


def write_sheet(workbook, sheet_name: str, columns: Iterable[str], rows: Iterable[tuple], used: set[str]) -> int:
    worksheet = workbook.create_sheet(safe_sheet_name(sheet_name, used))
    worksheet.append(list(columns))
    count = 0
    for row in rows:
        worksheet.append(list(row))
        count += 1
    worksheet.freeze_panes = "A2"
    return count


def autosize_workbook(workbook) -> None:
    for worksheet in workbook.worksheets:
        for column_cells in worksheet.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells[:100]:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            worksheet.column_dimensions[column_letter].width = min(max(max_length + 2, 10), 40)


def build_workbook(conn, args, biz_date: str):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    used_sheet_names: set[str] = set()
    summary = []

    with conn.cursor() as cursor:
        tables = all_date_tables(cursor, args.database) if args.all_date_tables else existing_default_tables(cursor, args.database)

        for table_name, date_column, display_name in tables:
            columns, rows = fetch_table(cursor, args.database, table_name, date_column, biz_date)
            if not rows and not args.include_empty_tables:
                continue
            row_count = write_sheet(workbook, display_name, columns, rows, used_sheet_names)
            summary.append((display_name, date_column, row_count))

    overview = workbook.create_sheet("汇总", 0)
    overview.append(["日期", biz_date])
    overview.append([])
    overview.append(["表名", "日期字段", "行数"])
    for row in summary:
        overview.append(list(row))
    overview.freeze_panes = "A4"
    autosize_workbook(workbook)
    return workbook, summary


def main() -> int:
    load_env()
    parser = argparse.ArgumentParser(description="Export Xiangwang daily database rows to Excel")
    parser.add_argument("--date", help="Business date, format YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--output", help="Output xlsx path. Defaults to exports/daily_database_YYYY-MM-DD.xlsx")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "3306")))
    parser.add_argument("--user", default=os.environ.get("USER", "remote_user"))
    parser.add_argument("--password", default=os.environ.get("PASS", "Tourism2024"))
    parser.add_argument("--database", default=os.environ.get("DATABASE", "Xiangwang"))
    parser.add_argument("--all-date-tables", action="store_true", help="Export every table with a recognized date column.")
    parser.add_argument("--include-empty-tables", action="store_true", help="Also create sheets for tables with no rows on the selected date.")
    args = parser.parse_args()

    biz_date = parse_date(args.date)
    output_path = Path(args.output) if args.output else PROJECT_ROOT / "exports" / f"daily_database_{biz_date}.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        conn = connect(args)
    except pymysql.err.OperationalError:
        if "--host" in os.sys.argv or args.host in ("127.0.0.1", "localhost"):
            raise
        args.host = "127.0.0.1"
        conn = connect(args)
    try:
        workbook, summary = build_workbook(conn, args, biz_date)
        workbook.save(output_path)
    finally:
        conn.close()

    print(f"output={output_path}")
    for table_name, date_column, row_count in summary:
        print(f"{table_name}\t{date_column}\t{row_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

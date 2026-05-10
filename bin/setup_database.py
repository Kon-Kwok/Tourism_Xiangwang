#!/usr/bin/env python3
"""Create the unified Xiangwang database schema."""

from __future__ import annotations

import os
from pathlib import Path

import pymysql


DB_UNIX_SOCKET = os.environ.get("MYSQL_SOCKET", "/var/run/mysqld/mysqld.sock")
DB_HOST = os.environ.get("HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("PORT", "3306"))
DB_USER = os.environ.get("MYSQL_USER", os.environ.get("DB_USER", "remote_user"))
DB_PASSWORD = os.environ.get("PASS", os.environ.get("MYSQL_PASSWORD", ""))
SCHEMA_FILE = Path("sql/Xiangwang/Xiangwang.sql")


def _connect(database: str | None = None):
    kwargs = {
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": database,
        "charset": "utf8mb4",
        "autocommit": False,
    }
    if DB_UNIX_SOCKET and Path(DB_UNIX_SOCKET).exists() and DB_HOST in {"localhost", "127.0.0.1"}:
        kwargs["unix_socket"] = DB_UNIX_SOCKET
    else:
        kwargs["host"] = DB_HOST
        kwargs["port"] = DB_PORT
    return pymysql.connect(**kwargs)


def _split_sql(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for raw_line in sql.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue
        current.append(raw_line)
        if line.endswith(";"):
            statement = "\n".join(current).strip().rstrip(";")
            if statement:
                statements.append(statement)
            current = []
    if current:
        statements.append("\n".join(current).strip())
    return statements


def main() -> int:
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(f"schema file not found: {SCHEMA_FILE}")

    sql = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = _split_sql(sql)
    with _connect() as conn:
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
        conn.commit()

    print(f"✓ Xiangwang schema created from {SCHEMA_FILE}")
    print(f"✓ Executed {len(statements)} SQL statements")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

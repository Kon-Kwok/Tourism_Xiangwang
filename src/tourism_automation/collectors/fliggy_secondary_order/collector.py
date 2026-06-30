"""Orchestrate secondary booking order collection with pagination."""

from __future__ import annotations

import json
import os
import pymysql
import sys
from pathlib import Path

from tourism_automation.collectors.fliggy_secondary_order.client import (
    SecondaryOrderClient,
)
from tourism_automation.collectors.fliggy_secondary_order.normalize import (
    parse_xml,
)

MAX_PAGES = 50  # safety limit


def _date_to_param(date_str: str) -> str:
    """Convert '2026-06-01' to '20260601-0000'."""
    return date_str.replace("-", "") + "-0000"


def _date_to_param_end(date_str: str) -> str:
    """Convert '2026-06-30' to '20260630-2350'."""
    return date_str.replace("-", "") + "-2350"


def collect_secondary_orders(
    start_date: str,
    end_date: str,
) -> tuple[list[dict], list[dict]]:
    """Collect all secondary booking orders for a date range.

    Args:
        start_date: Start date, e.g. '2026-06-01'.
        end_date: End date, e.g. '2026-06-30'.

    Returns:
        (orders, exceptions) tuple:
          orders: List of normalized order dicts.
          exceptions: List of dicts for orders with unparseable room_capacity.
    """
    apply_start = _date_to_param(start_date)
    apply_end = _date_to_param_end(end_date)

    client = SecondaryOrderClient.from_local_chrome()
    all_orders: list[dict] = []
    all_exceptions: list[dict] = []
    seen_ids: set[str] = set()

    for page_num in range(1, MAX_PAGES + 1):
        html = client.fetch_page(
            page_num=page_num,
            apply_start=apply_start,
            apply_end=apply_end,
        )

        page_orders, has_next, page_exceptions = parse_xml(html)

        for order in page_orders:
            oid = order["order_id"]
            if oid not in seen_ids:
                seen_ids.add(oid)
                all_orders.append(order)

        all_exceptions.extend(page_exceptions)

        if not has_next:
            break

    return all_orders, all_exceptions


def _read_env() -> dict:
    env_path = Path(__file__).resolve().parents[4] / ".env"
    result = {}
    if not env_path.exists():
        return result
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def store_orders(orders: list[dict]) -> int:
    """Store orders into Xiangwang.order_list_secondary.

    Upsert pattern: ON DUPLICATE KEY UPDATE ensures status changes are propagated
    (e.g. previously-valid → '商家已驳回').

    Returns number of rows inserted/updated.
    """
    if not orders:
        return 0

    env = _read_env()
    db_password = env.get("PASS") or os.environ.get("PASS")
    if not db_password:
        raise RuntimeError(
            "数据库密码未配置。请在项目根目录 .env 文件中设置 PASS=your_password，"
            "或设置环境变量 PASS"
        )
    conn = pymysql.connect(
        host=env.get("HOST") or os.environ.get("HOST", "127.0.0.1"),
        port=int(env.get("PORT") or os.environ.get("PORT", 3306)),
        user=env.get("USER") or os.environ.get("USER", "remote_user"),
        password=db_password,
        database="Xiangwang",
        charset="utf8mb4",
    )

    try:
        with conn.cursor() as cur:
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS `order_list_secondary` (
                  `id`            BIGINT NOT NULL AUTO_INCREMENT,
                  `order_id`      VARCHAR(50) NOT NULL COMMENT '订单编号',
                  `item_title`    VARCHAR(500) DEFAULT NULL COMMENT '商品标题',
                  `buy_mount`     INT DEFAULT NULL COMMENT '数量（I列）',
                  `room_capacity` INT DEFAULT NULL COMMENT '房型标注人数（Q列）',
                  `pax`           INT DEFAULT NULL COMMENT 'PAX = buy_mount × room_capacity',
                  `status_text`   VARCHAR(50) DEFAULT NULL COMMENT '订单状态（K列）',
                  `deal_time`     DATETIME DEFAULT NULL COMMENT '成交时间',
                  `submit_time`   DATETIME DEFAULT NULL COMMENT '提交时间',
                  `travel_date`   DATE DEFAULT NULL COMMENT '出行日期',
                  `price`         DECIMAL(10,2) DEFAULT NULL COMMENT '价格',
                  `created_at`    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  PRIMARY KEY (`id`),
                  UNIQUE KEY `uk_order_id` (`order_id`),
                  KEY `idx_submit_time` (`submit_time`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='飞猪二次预约订单数据'
            """)

            # Upsert each order — updates status_text/pax on duplicate order_id
            inserted = 0
            for o in orders:
                cur.execute(
                    """
                    INSERT INTO order_list_secondary
                    (order_id, item_title, buy_mount, room_capacity, pax,
                     status_text, deal_time, submit_time, travel_date, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                      buy_mount = VALUES(buy_mount),
                      room_capacity = VALUES(room_capacity),
                      pax = VALUES(pax),
                      status_text = VALUES(status_text),
                      submit_time = VALUES(submit_time),
                      travel_date = VALUES(travel_date),
                      price = VALUES(price)
                    """,
                    (
                        o["order_id"],
                        o.get("item_title"),
                        o.get("buy_mount"),
                        o.get("room_capacity"),
                        o.get("pax"),
                        o.get("status_text"),
                        o.get("deal_time"),
                        o.get("submit_time"),
                        o.get("travel_date"),
                        o.get("price"),
                    ),
                )
                inserted += 1

        conn.commit()
        return inserted
    finally:
        conn.close()


def collect_and_store(
    start_date: str,
    end_date: str,
    output: str | None = None,
) -> dict:
    """Collect and store secondary booking orders.

    Args:
        start_date: Start date, e.g. '2026-06-01'.
        end_date: End date, e.g. '2026-06-30'.
        output: Optional file path to write JSON result.

    Returns:
        Summary dict with order_count, stored_count, and exceptions.
    """
    orders, exceptions = collect_secondary_orders(start_date, end_date)

    # 房型人数解析异常：阻止 PAX 发布
    if exceptions:
        print(f"ERROR: {len(exceptions)} 条二次预约订单无法解析 Q 列房型人数，PAX 不可发布",
              file=sys.stderr)
        for exc in exceptions:
            print(f"  order_id={exc['order_id']} sku={exc['raw_sku_items']} "
                  f"buy_mount={exc['buy_mount']} status={exc['status_text']} "
                  f"submit_time={exc['submit_time']}",
                  file=sys.stderr)
        print("请人工核实以上订单的 Q 列房型标注人数后重新采集。", file=sys.stderr)

    stored = store_orders(orders)

    result = {
        "order_count": len(orders),
        "stored_count": stored,
        "exception_count": len(exceptions),
    }

    if output:
        import json as _json
        payload = {
            "summary": result,
            "rows": orders,
            "exceptions": exceptions,
        }
        with open(output, "w", encoding="utf-8") as f:
            _json.dump(payload, f, ensure_ascii=False, indent=2)

    return result

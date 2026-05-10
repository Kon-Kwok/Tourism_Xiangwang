"""Collector orchestration for Alimama daily advertising reports."""

from __future__ import annotations

from tourism_automation.collectors.alimama_daily.client import AlimamaDailyClient
from tourism_automation.collectors.alimama_daily.normalize import normalize_alimama_daily_payloads


def collect_alimama_daily(*, biz_date: str) -> dict:
    client = AlimamaDailyClient.from_local_chrome()
    star_store_payload = client.fetch_star_store(biz_date=biz_date)
    scene_payload = client.fetch_onebp_scene_report(biz_date=biz_date)
    return normalize_alimama_daily_payloads(
        biz_date=biz_date,
        star_store_payload=star_store_payload,
        scene_payload=scene_payload,
    )

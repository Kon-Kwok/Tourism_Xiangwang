"""Collector orchestration for the Fliggy star store report."""

from __future__ import annotations

from tourism_automation.collectors.fliggy_star_store.client import FliggyStarStoreClient
from tourism_automation.collectors.fliggy_star_store.normalize import normalize_star_store_payload


def collect_star_store(*, biz_date: str) -> dict:
    client = FliggyStarStoreClient.from_local_chrome()
    payload = client.fetch_report(biz_date=biz_date)
    return normalize_star_store_payload(payload, biz_date=biz_date)

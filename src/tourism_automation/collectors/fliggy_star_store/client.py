"""HTTP client for the Alimama star store report."""

from __future__ import annotations

from typing import Any

from tourism_automation.shared.chrome import ChromeHttpClient


STAR_STORE_REPORT_URL = "https://brandsearch.taobao.com/report/adrQuery/rptCampaignList2.json"
STAR_STORE_REFERER = "https://branding.taobao.com/"
STAR_STORE_PRODUCT_ID = "101005202"
STAR_STORE_EFFECT_CONVERSION_CYCLE = "3"
STAR_STORE_ATTRIBUTION = "click"
STAR_STORE_TRAFFIC_TYPE = "[1,2,4,5]"


class FliggyStarStoreClient:
    def __init__(self, http: ChromeHttpClient):
        self.http = http

    @classmethod
    def from_local_chrome(cls) -> "FliggyStarStoreClient":
        return cls(http=ChromeHttpClient.from_local_chrome())

    def fetch_report(self, *, biz_date: str) -> dict[str, Any]:
        response = self.http.session.get(
            STAR_STORE_REPORT_URL,
            params={
                "r": "mx_http",
                "startdate": biz_date,
                "enddate": biz_date,
                "productid": STAR_STORE_PRODUCT_ID,
                "effect": STAR_STORE_EFFECT_CONVERSION_CYCLE,
                "type": STAR_STORE_ATTRIBUTION,
                "sortby": "",
                "sortrule": "",
                "offset": 0,
                "pagesize": 20,
            },
            headers={
                "Referer": STAR_STORE_REFERER,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/plain, */*",
            },
            timeout=20,
        )
        if response.status_code == 403:
            raise RuntimeError(f"Star store report access denied: {response.text[:200]}")
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        text = response.text.lstrip()
        if text.lower().startswith("<!doctype html") or "<title>登录</title>" in text:
            raise RuntimeError("Star store report authentication failed: received login page HTML")
        if "json" not in content_type and not text.startswith("{"):
            raise RuntimeError(f"Star store report response is not JSON: {text[:200]}")
        return response.json()

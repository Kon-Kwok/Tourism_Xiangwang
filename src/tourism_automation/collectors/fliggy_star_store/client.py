"""CDP-based client for the Alimama star store report.

Calls the brandsearch API via Chrome DevTools Protocol on the branding.taobao.com
page, so the request carries the page's live session cookies and CSRF tokens,
avoiding the 403 anti-bot blocking that direct HTTP received.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from tourism_automation.shared.cdp_client import create_cdp_client

STAR_STORE_REPORT_URL = "https://brandsearch.taobao.com/report/adrQuery/rptCampaignList2.json"
STAR_STORE_PRODUCT_ID = "101005202"
STAR_STORE_EFFECT_CONVERSION_CYCLE = "3"
STAR_STORE_ATTRIBUTION = "click"


class FliggyStarStoreClient:
    def __init__(self, http: Any = None):
        pass  # http arg kept for caller compatibility, no longer used

    @classmethod
    def from_local_chrome(cls) -> "FliggyStarStoreClient":
        return cls()

    def fetch_report(self, *, biz_date: str) -> dict[str, Any]:
        cdp = create_cdp_client()
        params = urlencode({
            "r": "mx_http",
            "startdate": biz_date,
            "enddate": biz_date,
            "productid": STAR_STORE_PRODUCT_ID,
            "effect": STAR_STORE_EFFECT_CONVERSION_CYCLE,
            "type": STAR_STORE_ATTRIBUTION,
            "sortby": "",
            "sortrule": "",
            "offset": "0",
            "pagesize": "20",
        })
        full_url = f"{STAR_STORE_REPORT_URL}?{params}"

        tab = cdp.find_tab_by_url_pattern("branding.taobao.com")
        js = f"""
        (async () => {{
            try {{
                const resp = await fetch("{full_url}", {{
                    credentials: "include",
                    headers: {{"Accept": "application/json"}}
                }});
                const text = await resp.text();
                return JSON.stringify({{status: resp.status, body: text}});
            }} catch (e) {{
                return JSON.stringify({{error: e.message}});
            }}
        }})()
        """
        result = cdp.execute_js(tab["ws_url"], js)
        if result.get("error"):
            raise RuntimeError(f"Star store API call failed: {result['error']}")
        status = result.get("status", 0)
        body = result.get("body", "")
        if status == 403 or "access denied" in body.lower():
            raise RuntimeError(f"Star store report access denied (403)")
        if status != 200:
            raise RuntimeError(f"Star store report HTTP {status}: {body[:200]}")
        import json
        return json.loads(body)

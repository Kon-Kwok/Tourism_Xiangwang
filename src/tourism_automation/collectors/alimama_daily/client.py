"""HTTP clients for Alimama daily advertising reports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from tourism_automation.collectors.fliggy_star_store.client import FliggyStarStoreClient
from tourism_automation.shared.cdp_client import CdpClient
from tourism_automation.shared.chrome import ChromeHttpClient


ONE_ALIMAMA_REPORT_URL = "https://one.alimama.com/report/query.json"
ONE_ALIMAMA_REFERER = "https://one.alimama.com/index.html"
ONE_ALIMAMA_FIELDS = [
    "adPv",
    "click",
    "ctr",
    "charge",
    "ecpc",
    "cvr",
    "alipayInshopNum",
    "alipayInshopAmt",
    "roi",
    "cartInshopNum",
    "itemColInshopNum",
    "shopColDirNum",
    "cartRate",
    "colNum",
    "itemColInshopCost",
    "cartCost",
    "itemColInshopRate",
]


@dataclass
class OneAlimamaTokens:
    csrf_id: str
    login_point_id: str


class AlimamaDailyClient:
    def __init__(self, http: ChromeHttpClient, tokens: OneAlimamaTokens | None = None):
        self.http = http
        self.tokens = tokens

    @classmethod
    def from_local_chrome(cls) -> "AlimamaDailyClient":
        return cls(http=ChromeHttpClient.from_local_chrome())

    def fetch_star_store(self, *, biz_date: str) -> dict[str, Any]:
        return FliggyStarStoreClient(self.http).fetch_report(biz_date=biz_date)

    def fetch_onebp_scene_report(self, *, biz_date: str) -> dict[str, Any]:
        tokens = self.tokens or discover_one_alimama_tokens()
        payload = {
            "bizCode": "universalBP",
            "fromRealTime": False,
            "source": "baseReport",
            "byPage": True,
            "totalTag": True,
            "needCountAccelerate": True,
            "byPageWithoutCount": False,
            "rptType": "account",
            "pageSize": 20,
            "havingList": [],
            "endTime": biz_date,
            "unifyType": "zhai",
            "effectEqual": 3,
            "startTime": biz_date,
            "splitType": "day",
            "queryFieldIn": ONE_ALIMAMA_FIELDS,
            "queryDomains": ["scene"],
            "csrfId": tokens.csrf_id,
            "loginPointId": tokens.login_point_id,
        }
        response = self.http.session.post(
            ONE_ALIMAMA_REPORT_URL,
            params={"csrfId": tokens.csrf_id, "bizCode": "universalBP"},
            json=payload,
            headers={
                "Referer": ONE_ALIMAMA_REFERER,
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
                "bx-v": "2.5.36",
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        info = data.get("info") or {}
        if info.get("ok") is False:
            raise RuntimeError(f"One Alimama report API failed: {info.get('message') or data}")
        return data


def discover_one_alimama_tokens() -> OneAlimamaTokens:
    """Read the current report page tokens from the local Chrome debug session.

    The business payloads are fetched through HTTP requests. This helper only avoids
    hard-coding volatile csrf/loginPoint tokens by reading already loaded request
    metadata from Chrome.
    """

    cdp = CdpClient()
    for page in cdp.list_tabs():
        if page.get("type") != "page" or "one.alimama.com" not in page.get("url", ""):
            continue
        value = cdp.execute_js(page["webSocketDebuggerUrl"], _TOKEN_DISCOVERY_EXPR)
        tokens = _tokens_from_text(json.dumps(value, ensure_ascii=False))
        if tokens:
            return tokens
    raise RuntimeError("未找到已打开的 one.alimama.com 报表页，无法发现 csrfId/loginPointId")


def _tokens_from_text(text: str) -> OneAlimamaTokens | None:
    csrf_match = re.search(r"csrfId[=\":\"%3D]+([A-Za-z0-9_-]+(?:_[0-9]+){3})", text)
    login_match = re.search(r"loginPointId[=\":\"%3D]+([0-9A-Za-z_-]+)", text)
    if csrf_match and login_match:
        return OneAlimamaTokens(csrf_id=csrf_match.group(1), login_point_id=login_match.group(1))
    return None


_TOKEN_DISCOVERY_EXPR = """
(() => {
  const urls = performance.getEntriesByType('resource')
    .map(e => e.name)
    .filter(u => u.includes('csrfId=') || u.includes('loginPointId='));
  return {href: location.href, urls, now: Date.now()};
})()
"""

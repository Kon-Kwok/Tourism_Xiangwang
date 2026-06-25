"""CDP-based client for fetching secondary booking order HTML pages.

Uses Chrome DevTools Protocol to execute fetch() inside the browser context,
avoiding the need for cookie decryption on macOS.
"""

from __future__ import annotations

import json
import time

from tourism_automation.shared.cdp_client import CdpClient

BOOK_INFO_URL = (
    "https://yuyue.fliggy.com/travelbm/sell/bookInfoList.htm"
    "?pageNum={page_num}&status=100"
    "&applyTimeStart={apply_start}&applyTimeEnd={apply_end}"
)
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2.0
YUYUE_URL_PATTERN = "yuyue.fliggy.com"


class SecondaryOrderClient:
    """CDP client that fetches bookInfoList.htm via browser fetch()."""

    def __init__(self, cdp: CdpClient, ws_url: str):
        self.cdp = cdp
        self.ws_url = ws_url

    @classmethod
    def from_local_chrome(cls) -> "SecondaryOrderClient":
        cdp = CdpClient()
        tab = cdp.find_tab_by_url_pattern(YUYUE_URL_PATTERN)
        return cls(cdp=cdp, ws_url=tab["ws_url"])

    def fetch_page(
        self,
        page_num: int,
        apply_start: str,
        apply_end: str,
    ) -> str:
        """Fetch a single page of secondary booking orders via CDP fetch.

        Args:
            page_num: Page number (1-based).
            apply_start: Submit time start, e.g. '20260601-0000'.
            apply_end: Submit time end, e.g. '20260630-2350'.

        Returns:
            Raw HTML text of the page.
        """
        url = BOOK_INFO_URL.format(
            page_num=page_num,
            apply_start=apply_start,
            apply_end=apply_end,
        )

        # JavaScript fetch in browser context (uses existing cookies)
        js_code = f"""
        (async () => {{
            const resp = await fetch({json.dumps(url)}, {{
                method: 'GET',
                headers: {{ 'Accept': 'text/html' }}
            }});
            if (!resp.ok) {{
                return JSON.stringify({{error: 'HTTP ' + resp.status}});
            }}
            const text = await resp.text();
            return JSON.stringify({{html: text}});
        }})()
        """

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = self.cdp.execute_js(
                    self.ws_url, js_code, timeout=30, await_promise=True
                )
                if isinstance(result, str):
                    result = json.loads(result)
                if isinstance(result, dict) and "html" in result:
                    return result["html"]
                if isinstance(result, dict) and "error" in result:
                    raise RuntimeError(result["error"])
            except Exception as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)

        raise RuntimeError(
            f"Failed to fetch {url} after {MAX_RETRIES} attempts"
        ) from last_error

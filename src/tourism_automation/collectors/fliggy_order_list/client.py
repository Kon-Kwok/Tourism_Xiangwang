from __future__ import annotations

import json
import time

from tourism_automation.shared.chrome import ChromeHttpClient


ORDER_LIST_URL = "https://sell.fliggy.com/orderlist/ajax/orderList.htm?_input_charset=UTF-8&_output_charset=UTF-8"
ORDER_LIST_REFERER = "https://fsc.fliggy.com/"
TOKEN_DOMAIN_PRIORITY = (
    "sell.fliggy.com",
    ".fliggy.com",
    "fliggy.com",
    "fsc.fliggy.com",
    "seller.fliggy.com",
    ".taobao.com",
    "taobao.com",
)
ORDER_LIST_TRANSIENT_ERROR = "订单搜索失败，请稍后再试"
ORDER_LIST_MAX_ATTEMPTS = 8
ORDER_LIST_RETRY_DELAY_SECONDS = 2.0


def parse_order_list_response(raw_text: str) -> dict:
    text = raw_text.lstrip()
    lower_text = text.lower()
    if lower_text.startswith("<!doctype html") or "<title>登录</title>" in text:
        raise RuntimeError("Order list authentication failed: received login page HTML")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        preview = text[:200]
        raise RuntimeError(f"Order list response is not valid JSON: {preview}") from exc
    return payload["result"]


class FliggyOrderListClient:
    def __init__(self, http: ChromeHttpClient):
        self.http = http

    @classmethod
    def from_local_chrome(cls) -> "FliggyOrderListClient":
        return cls(http=ChromeHttpClient.from_local_chrome())

    def _get_tb_token(self) -> str:
        if not hasattr(self.http.session.cookies, "__iter__"):
            token = self.http.session.cookies.get("_tb_token_")
            if token:
                return token
            raise RuntimeError("Missing _tb_token_ in Chrome cookie session")

        token_candidates = []
        for cookie in self.http.session.cookies:
            if cookie.name == "_tb_token_":
                token_candidates.append(cookie)

        for domain in TOKEN_DOMAIN_PRIORITY:
            for cookie in token_candidates:
                if cookie.domain == domain:
                    return cookie.value

        if token_candidates:
            return token_candidates[0].value

        raise RuntimeError("Missing _tb_token_ in Chrome cookie session")

    def fetch_order_list(
        self,
        *,
        page_num: int,
        page_size: int,
        biz_type: int = 0,
        sort_field_enum: str = "ORDER_CREATE_TIME_DESC",
        deal_start: str,
        deal_end: str,
    ) -> dict:
        token = self._get_tb_token()
        last_payload = None
        for attempt in range(1, ORDER_LIST_MAX_ATTEMPTS + 1):
            response = self.http.session.post(
                ORDER_LIST_URL,
                headers={
                    "Referer": ORDER_LIST_REFERER,
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "*/*",
                },
                files=[
                    ("_tb_token_", (None, token)),
                    ("bizType", (None, str(biz_type))),
                    ("sortFieldEnum", (None, sort_field_enum)),
                    ("pageNum", (None, str(page_num))),
                    ("pageSize", (None, str(page_size))),
                    ("orderCreateTime", (None, f"{deal_start}~{deal_end}")),
                ],
                timeout=20,
            )
            payload = parse_order_list_response(response.text)
            if payload.get("success", True):
                return payload

            last_payload = payload
            if payload.get("errorMsg") != ORDER_LIST_TRANSIENT_ERROR or attempt == ORDER_LIST_MAX_ATTEMPTS:
                return payload

            time.sleep(ORDER_LIST_RETRY_DELAY_SECONDS)

        return last_payload or {}

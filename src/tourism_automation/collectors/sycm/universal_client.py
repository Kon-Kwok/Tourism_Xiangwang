"""通用的SYCM多页面数据采集客户端

此客户端支持采集SYCM不同页面的数据，使用统一的Chrome登录态。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from tourism_automation.collectors.sycm.pages import (
    SycmPage,
    ApiEndpoint,
    get_page,
    get_page_endpoints,
    build_api_url,
    list_pages,
)
from tourism_automation.shared.chrome import ChromeHttpClient


@dataclass
class PageDataResult:
    """页面数据采集结果"""
    page_id: str
    page_name: str
    endpoint_name: str
    status: str  # "success" or "error"
    data: Optional[Dict[str, object]] = None
    error: Optional[str] = None
    url: Optional[str] = None


@dataclass
class UniversalSycmClient:
    """通用SYCM客户端

    支持采集不同SYCM页面的数据
    """
    http: ChromeHttpClient | None = None

    def __post_init__(self):
        if self.http is None:
            self.http = ChromeHttpClient.from_local_chrome()

    def fetch_page_endpoint(
        self,
        page_id: str,
        endpoint_name: str,
        date_range: str,
        **kwargs
    ) -> PageDataResult:
        """采集指定页面的单个端点数据

        Args:
            page_id: 页面ID，如 "home", "flow_monitor"
            endpoint_name: 端点名称，如 "overview", "trend"
            date_range: 日期范围，如 "2026-04-19|2026-04-19"
            **kwargs: 额外的查询参数

        Returns:
            PageDataResult对象
        """
        page = get_page(page_id)
        if not page:
            return PageDataResult(
                page_id=page_id,
                page_name="Unknown",
                endpoint_name=endpoint_name,
                status="error",
                error=f"Page not found: {page_id}"
            )

        url = build_api_url(page_id, endpoint_name, date_range, **kwargs)
        if not url:
            return PageDataResult(
                page_id=page_id,
                page_name=page.name,
                endpoint_name=endpoint_name,
                status="error",
                error=f"Endpoint not found: {endpoint_name}"
            )

        try:
            data = self.http.fetch_json(url, referer=page.url)
            return PageDataResult(
                page_id=page_id,
                page_name=page.name,
                endpoint_name=endpoint_name,
                status="success",
                data=data,
                url=url
            )
        except Exception as e:
            return PageDataResult(
                page_id=page_id,
                page_name=page.name,
                endpoint_name=endpoint_name,
                status="error",
                error=str(e),
                url=url
            )

    def fetch_page_all_endpoints(
        self,
        page_id: str,
        date_range: str,
        **kwargs
    ) -> List[PageDataResult]:
        """采集指定页面的所有端点数据

        Args:
            page_id: 页面ID
            date_range: 日期范围
            **kwargs: 额外的查询参数

        Returns:
            PageDataResult列表
        """
        page = get_page(page_id)
        if not page:
            return [PageDataResult(
                page_id=page_id,
                page_name="Unknown",
                endpoint_name="all",
                status="error",
                error=f"Page not found: {page_id}"
            )]

        results = []
        for endpoint in page.endpoints:
            result = self.fetch_page_endpoint(
                page_id, endpoint.name, date_range, **kwargs
            )
            results.append(result)

        return results

    def fetch_multiple_pages(
        self,
        page_ids: List[str],
        date_range: str,
        **kwargs
    ) -> Dict[str, List[PageDataResult]]:
        """采集多个页面的数据

        Args:
            page_ids: 页面ID列表
            date_range: 日期范围
            **kwargs: 额外的查询参数

        Returns:
            字典，key为page_id，value为该页面的采集结果列表
        """
        results = {}
        for page_id in page_ids:
            results[page_id] = self.fetch_page_all_endpoints(page_id, date_range, **kwargs)
        return results

    def list_available_pages(self) -> List[str]:
        """列出所有可用的页面"""
        return list_pages()

    def list_page_endpoints(self, page_id: str) -> List[str]:
        """列出指定页面的所有端点"""
        endpoints = get_page_endpoints(page_id)
        return [ep.name for ep in endpoints]

    def get_page_info(self, page_id: str) -> Optional[Dict[str, object]]:
        """获取页面信息"""
        page = get_page(page_id)
        if not page:
            return None

        return {
            "page_id": page.page_id,
            "name": page.name,
            "url": page.url,
            "api_prefix": page.api_prefix,
            "endpoints": [
                {
                    "name": ep.name,
                    "path": ep.path,
                    "required_params": ep.required_params
                }
                for ep in page.endpoints
            ]
        }


# 首页专用客户端接口
class SycmHomeClient:
    """首页专用客户端"""

    def __init__(self, http: ChromeHttpClient | None = None):
        self.universal_client = UniversalSycmClient(http)

    def fetch_home_payloads(self, biz_date: str):
        """采集首页数据（保持原有接口）"""
        results = self.universal_client.fetch_page_all_endpoints(
            "home",
            f"{biz_date}|{biz_date}"
        )

        # 按原有顺序返回：overview, trend, table
        overview_data = next(
            (r.data for r in results if r.endpoint_name == "overview"),
            {}
        )
        trend_data = next(
            (r.data for r in results if r.endpoint_name == "trend"),
            {}
        )
        table_data = next(
            (r.data for r in results if r.endpoint_name == "table"),
            {}
        )

        return overview_data, trend_data, table_data

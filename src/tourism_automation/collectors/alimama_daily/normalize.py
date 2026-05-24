"""Normalize Alimama daily advertising payloads."""

from __future__ import annotations

from typing import Any

from tourism_automation.collectors.alimama_daily.excel_rules import calculate_excel_metrics, calculate_wanxiangtai_2_total
from tourism_automation.collectors.alimama_daily.metrics import base_metrics
from tourism_automation.collectors.fliggy_star_store.normalize import normalize_star_store_payload


SCENE_TO_CHANNEL = {
    "关键词推广": "tmall_express",
    "人群推广": "gravity_rubiks_cube",
    "超级短视频": "wanxiangtai_short_video",
    "超级直播": "wanxiangtai_live",
    "货品运营": "wanxiangtai_goods_operation",
    "货品全站推广": "wanxiangtai_full_site",
    "全站推广": "wanxiangtai_full_site",
}


def normalize_alimama_daily_payloads(
    *,
    biz_date: str,
    star_store_payload: dict[str, Any],
    scene_payload: dict[str, Any],
) -> dict[str, Any]:
    star_store = normalize_star_store_payload(star_store_payload, biz_date=biz_date)
    scene_rows = _extract_scene_rows(scene_payload)
    channels: dict[str, dict[str, Any]] = {}
    if star_store.get("status") == "success":
        channels["star_store"] = star_store["metrics"]
    elif star_store.get("status") == "no_data":
        channels["star_store"] = _zero_metrics(biz_date)

    for scene_name, channel in SCENE_TO_CHANNEL.items():
        row = scene_rows.get(scene_name)
        if row:
            channels[channel] = _metrics_from_onebp_scene(row, biz_date=biz_date, channel=channel)
        elif channel in {"tmall_express", "gravity_rubiks_cube"}:
            channels[channel] = _zero_metrics(biz_date)

    wanxiangtai_2_rows = {
        "超级短视频": channels.get("wanxiangtai_short_video", _zero_metrics(biz_date)),
        "超级直播": channels.get("wanxiangtai_live", _zero_metrics(biz_date)),
        "货品运营": channels.get("wanxiangtai_goods_operation", _zero_metrics(biz_date)),
        "全站推广": channels.get("wanxiangtai_full_site", _zero_metrics(biz_date)),
    }
    for data_source, metrics in wanxiangtai_2_rows.items():
        metrics["data_source"] = data_source
    wanxiangtai_total = _sum_metrics(list(wanxiangtai_2_rows.values()), biz_date=biz_date)
    wanxiangtai_total["data_source"] = "小计"
    wanxiangtai_2_rows["小计"] = wanxiangtai_total
    channels["wanxiangtai"] = wanxiangtai_total

    missing = _missing_channels(channels)
    return {
        "status": "success" if not missing else "partial",
        "date_time": biz_date,
        "channels": channels,
        "wanxiangtai_2_rows": wanxiangtai_2_rows,
        "missing_channels": missing,
        "raw": {
            "star_store": star_store_payload,
            "onebp_scene": scene_payload,
        },
    }


def _extract_scene_rows(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = payload.get("data", {}).get("list") or []
    return {row.get("scene1Name"): row for row in rows if row.get("scene1Name")}


def _metrics_from_onebp_scene(row: dict[str, Any], *, biz_date: str, channel: str) -> dict[str, Any]:
    sheet = channel if channel in {"tmall_express", "gravity_rubiks_cube"} else "wanxiangtai_2"
    return calculate_excel_metrics(
        {
            "cost": row.get("charge"),
            "imp": row.get("adPv"),
            "click": row.get("click"),
            "order_count": row.get("alipayInshopNum"),
            "sales": row.get("alipayInshopAmt"),
            "shopping_cart": row.get("cartInshopNum"),
            "bookmark_product": row.get("itemColInshopNum"),
            "bookmark_store": row.get("shopColDirNum"),
        },
        date_time=biz_date,
        sheet=sheet,
    )


def _zero_metrics(biz_date: str) -> dict[str, Any]:
    return base_metrics(
        {
            "cost": 0,
            "imp": 0,
            "click": 0,
            "order_count": 0,
            "sales": 0,
            "shopping_cart": 0,
            "bookmark_product": 0,
            "bookmark_store": 0,
        },
        date_time=biz_date,
    )


def _sum_metrics(rows: list[dict[str, Any]], *, biz_date: str) -> dict[str, Any]:
    return calculate_wanxiangtai_2_total(rows, date_time=biz_date)


def _missing_channels(channels: dict[str, dict[str, Any]]) -> list[str]:
    required = [
        "star_store",
        "tmall_express",
        "gravity_rubiks_cube",
        "wanxiangtai",
    ]
    return [name for name in required if name not in channels]

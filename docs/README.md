# 文档说明

`docs/` 只保留对开发、运维和功能扩展有直接指导意义的内容。阶段性汇报、一次性分析结果和测试样本不再保留。

## 建议阅读顺序

1. [architecture/project-structure.md](architecture/project-structure.md)：了解目录结构、模块边界和 CLI 入口。
2. [collectors/unified_chrome_guide.md](collectors/unified_chrome_guide.md)：准备统一 Chrome 调试会话。
3. [operations/openclaw-daily-report-runbook.md](operations/openclaw-daily-report-runbook.md)：OpenClaw 代理执行日报采集、入库和校验的标准流程。
4. 按目标功能阅读对应采集器文档：
   - [collectors/sycm.md](collectors/sycm.md)
   - [collectors/sycm_multi_page.md](collectors/sycm_multi_page.md)
   - [collectors/fliggy-home.md](collectors/fliggy-home.md)
   - [collectors/fliggy_kpi_usage.md](collectors/fliggy_kpi_usage.md)
   - [collectors/shop_kpi_export_guide.md](collectors/shop_kpi_export_guide.md)
   - `python3 -m tourism_automation.cli.main fliggy-order-list list --page-num 1 --page-size 10 --all-pages`：飞猪订单列表纯 HTTP 采集
   - `python3 -m tourism_automation.cli.main fliggy-order-list list --page-num 1 --page-size 100 --all-pages --deal-start "2026-04-20 00:00:00" --deal-end "2026-04-20 23:59:59" | python3 bin/prepare_order_list_for_storage.py`：飞猪订单列表采集后做入库前汇总处理，结果需要分别进入 `prepare_order_list_sql.py` 和 `prepare_shop_daily_key_sql.py`

## 保留的参考文档

- [sycm_shop_source_api.md](sycm_shop_source_api.md)：SYCM 店铺来源接口参数和响应格式。
- [implementation/fliggy_kpi_implementation.md](implementation/fliggy_kpi_implementation.md)：飞猪 KPI 采集实现背景和代码路径。
- 飞猪订单列表采集当前为纯 `HTTP + Cookie` 实现，CDP 仅用于前期定位接口与参数。
- 日报订单链路需要额外写入 `Xiangwang.shop_daily_key_data` 的 `total_bookings`、`total_pax`、`gmv`，以 `skills/skills/openclaw-daily-data-collection/SKILL.md` 为准。

## 维护原则

- 优先保留“怎么运行、怎么排查、怎么扩展”。
- 重复内容合并到单一文档，不保留平行摘要。
- 临时分析结果和导出的原始样本不进入长期文档集合。

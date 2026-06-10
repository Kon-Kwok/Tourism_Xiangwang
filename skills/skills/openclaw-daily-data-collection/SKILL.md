---
name: openclaw-daily-data-collection
description: OpenClaw 侧采集并补齐 Xiangwang 店铺每日登记数据；当前保留 SYCM 服务核心监控（咨询人数）、飞猪订单、新 GMV 采集（日历房+度假订单）、SYCM 流量作为必要数据源，赤兔 KPI 和阿里妈妈投放采集已停用。
---

# OpenClaw 每日数据采集技能

调用项目根目录的 `scripts/all.sh` 完成"店铺每日登记"数据采集。当前流程保留 SYCM 服务核心监控（咨询人数）、飞猪订单、新 GMV 采集（日历房+度假订单）、SYCM 流量看板作为必要数据源，赤兔 KPI 和阿里妈妈投放日报已停用（保留为注释）。

## 快速开始

所有命令都在项目根目录执行：

```bash
cd ~/Tourism_Xiangwang

# 不传日期默认采集昨天
./scripts/all.sh

# 采集指定日期
./scripts/all.sh 2026-05-01
```

单独采集：

```bash
./scripts/sycm_service.sh 2026-05-01    # 咨询人数（SYCM 服务核心监控）
./scripts/fliggy_orders.sh 2026-05-01    # 下单买家数（飞猪订单列表）
./scripts/gmv_combined.sh 2026-05-01     # GMV（链路1 日历房 + 链路2 度假订单）
./scripts/sycm_flow.sh 2026-05-01       # PV / UV / PaidUV / 关注店铺人数
# ./scripts/kpi_reports.sh 2026-05-01    # 赤兔KPI（已停用）
# ./scripts/alimama_daily.sh 2026-05-01  # 阿里妈妈（已停用）
./scripts/apply_cross_table_rules.sh 2026-05-01
```

## 日期规则

- 日报采集必须固定为同一天：开始日期 = 结束日期 = `YYYY-MM-DD`。
- 用户说"5月1日日报"时，按当前年份解析为 `YYYY-05-01`；没有日期时执行昨天。

## 前置条件

- 使用统一 Chrome 调试窗口：`~/Tourism_Xiangwang/bin/start-chrome-unified.sh`
- Chrome 里已登录 `sycm.taobao.com`、`fsc.fliggy.com`、`sell.fliggy.com`
  - 赤兔（`kf.topchitu.com`）和阿里妈妈（`one.alimama.com`/`brandsearch.taobao.com`）已停用，不再需要登录
- 项目根目录 `.env` 已配置数据库连接，脚本会自动加载：

```bash
HOST=localhost
PORT=3306
USER=remote_user
PASS=your_mysql_password
```

## 目标表

| 业务 | 目标表 | 状态 |
|---|---|---|
| SYCM 服务核心监控（咨询人数） | `Xiangwang.shop_data_daily_registration`（直接写入） | ✅ 当前 |
| 飞猪订单列表 | `Xiangwang.order_list`、`Xiangwang.shop_daily_key_data` | ✅ 当前 |
| 新 GMV 采集（双链路） | `Xiangwang.shop_daily_key_data`（gmv 字段） | ✅ 当前 |
| SYCM 流量看板 | `Xiangwang.shop_daily_key_data`、`Xiangwang.shop_data_daily_registration` | ✅ 当前 |
| 赤兔 KPI 客服报表 | `Xiangwang.customer_service_data_daily`、`Xiangwang.customer_service_performance_summary`、`Xiangwang.customer_service_performance_workload_analysis` | 🚫 已停用 |
| 阿里妈妈投放日报 | `Xiangwang.star_store`、`Xiangwang.tmall_express`、`Xiangwang.gravity_rubiks_cube`、`Xiangwang.wanxiangtai`、`Xiangwang.wanxiangtai_2` | 🚫 已停用 |

`Xiangwang.shop_daily_key_data` 的 `日期` 索引可能非唯一，写入必须保持 `UPDATE` 后 `INSERT ... WHERE NOT EXISTS`，不要改回 `ON DUPLICATE KEY UPDATE`。

## 最终表字段来源

`Xiangwang.shop_data_daily_registration` 十个字段：

| 字段 | 数据源 | 获取方式 |
|---|---|---|
| 日期 | 脚本参数 | 直接设置 |
| PV | SYCM 流量监控 | `total_pv` |
| UV | SYCM 流量监控 | `total_uv` |
| PaidUV | SYCM 店铺来源 | `流量来源广告_uv` + `流量来源平台_uv` |
| 关注店铺人数 | SYCM 流量监控 | 直接写入 |
| GMV | 新 GMV（双链路） | 链路1(日历房 `checkOutRoomPrice`) + 链路2(度假订单导出 `总金额`，排除付款时间空白) |
| 咨询人数 | SYCM 服务核心监控 | API `cstUv1d` 直接写入 |
| 咨询转化率 | 计算 | `下单买家数 / 咨询人数` |
| 下单买家数 | 飞猪订单 | `total_bookings` |
| 下单转化率 | 计算 | `下单买家数 / UV` |

## 关键口径

### SYCM 服务核心监控（咨询人数）

- API：`https://sycm.taobao.com/csp/api/core/monitor/overview/list`
- 页面：`https://sycm.taobao.com/qos/service/core_monitor/new`
- 参数：`dateType=day&dateRange=1d&startDate=YYYYMMDD&endDate=YYYYMMDD`
- 字段：`data.data[].key == "cstUv1d"` → `value`
- 直接写入 `shop_data_daily_registration.咨询人数`，不再经过 `customer_service_performance_summary`

### 飞猪订单

- 必须带 `--all-pages`。
- 订单明细进入 `Xiangwang.order_list`。
- 订单汇总必须先经过 `bin/prepare_order_list_for_storage.py`，再由 `bin/prepare_shop_daily_key_sql.py` 写入 `total_bookings`、`total_pax`。
- `gmv` 现由 `gmv_combined.sh` 独立采集（双链路），`fliggy_orders.sh` 不再负责 GMV 计算。

### 新 GMV（双链路）

- **链路1 日历房**：调用 `hotel.fliggy.com/ota/reactjs/order_search.htm`，分页加总 `checkOutRoomPrice`
- **链路2 度假订单**：触发报表导出 → 轮询下载 → 解析 `.xls` → 排除 `付款时间` 为空白 → 加总 `总金额`
- 总 GMV = 链路1 + 链路2，写入 `shop_daily_key_data.gmv`
- 脚本：`bin/prepare_gmv_combined_to_json.py` → `bin/prepare_gmv_combined_sql.py`

### 阿里妈妈投放（已停用）

明星店铺接口：`https://brandsearch.taobao.com/report/adrQuery/rptCampaignList2.json`
one.alimama 场景接口：`https://one.alimama.com/report/query.json`
日期参数 `startTime/startdate = endTime/enddate = YYYY-MM-DD`。
固定口径：`effectConversionCycle/effectEqual = 3`，归因 `click`。
不给明星店铺接口传错误 `csrfID`。
入库时展示型字段按文本保存：`cost/sales/cpc/cpm/asp/cporder/cpshopping_cart/collection_cart_cost` 记为 `￥1,234.56`，`ctr/cvr/cart_rate/collection_cart_rate` 记为 `5.00%`；`roi` 和各类数量字段仍保留数值。

阿里妈妈公式按同一行基础字段计算：

- `CTR 点击率 = Click / IMP`
- `CPC 点击成本 = Cost / Click`
- `CPM 拉新成本 = (Cost / IMP) * 1000`
- `ROI 投资回报率 = Sales / Cost`
- `CVR 点击转化率 = Order / Click`
- `收藏加购量 = ShoppingCart + Bookmark-Product`
- `收藏加购成本 = Cost / 收藏加购量`
- `收藏加购率 = 收藏加购量 / Click`

## 跨表规则（采集完成后自动应用）

采集阶段各脚本只负责写入各自的基础表，跨表衍生字段由 `scripts/apply_cross_table_rules.sh` 统一补齐。当前只执行"店铺每日登记"所需规则，其余规则保留为注释：

### 停用规则：阿里妈妈投放数据 → shop_daily_key_data
| 源表 | 目标字段 |
|------|----------|
| `star_store.cost/imp/click` | `pingxiaobao_cost/imp/click` |
| `tmall_express.cost/imp/click` | `tmall_express_cost/imp/click` |
| `gravity_rubiks_cube.cost/imp/click` | `gravity_rubiks_cube_cost/imp/click` |
| `wanxiangtai.cost/imp/click` | `mansa_dae_cost/views/click` |

注意：阿里妈妈表 cost 字段存储为 `￥1,234.56` 格式，写入 shop_daily_key_data 前须 `CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL)` 去除货币符号。

### 停用规则：赤兔 KPI 咨询人数汇总 → 店铺每日登记
~~`customer_service_performance_summary` 所有客服 `咨询人数` SUM → `shop_data_daily_registration.咨询人数`~~

咨询人数现由 `sycm_service.sh` 直接从 SYCM 服务页面写入 `shop_data_daily_registration`，不再依赖赤兔。

### 停用规则：KPI 询单人数汇总 → chat_volume / 四个渠道 booked_cabin
已停用，保留为注释。

### 当前执行：[1/3] 流量来源汇总
- `流量来源汇总` = `流量来源广告_uv` + `流量来源平台_uv`

### 当前执行：[2/3] shop_daily_key_data → shop_data_daily_registration
| 源字段 | 目标字段 |
|--------|----------|
| `total_pv` | `PV` |
| `total_uv` | `UV` |
| `gmv` | `GMV` |
| `流量来源汇总` | `PaidUV` |
| `total_bookings` | `下单买家数` |

### 当前执行：[3/3] 转化率公式（shop_data_daily_registration 内横向计算）
- `咨询转化率` = `下单买家数 / 咨询人数`
- `下单转化率` = `下单买家数 / UV`

## 执行流程

```
开始
  ↓
1. SYCM 服务核心监控采集（咨询人数）
   - API 读取 cstUv1d → 直接写入 shop_data_daily_registration
   ↓
2. 飞猪订单列表采集
   - HTTP采集（--all-pages）→ 预处理 → 订单明细入库 → 订单汇总入库（下单买家数）
   ↓
3. 新 GMV 采集（日历房 + 度假订单）
   - 链路1: hotel.fliggy.com 日历房分页加总 checkOutRoomPrice
   - 链路2: sell.fliggy.com 度假订单导出 → 下载 .xls → 排除付款时间空白 → 加总总金额
   - 写入 shop_daily_key_data.gmv
   ↓
4. SYCM 流量看板采集
   - HTTP采集 → 转换SQL（含关注店铺人数）→ 入库
   ↓
5. 跨表规则应用（补齐店铺每日登记字段）
   - 流量来源汇总
   - shop_daily_key_data → shop_data_daily_registration
   - 转化率计算
   ↓
完成
```

## 数据管理规范

### 采集
- 采集新日期数据时，只追加不清理已有数据
- 采集完成后，对表按日期重排（`DELETE` + `INSERT ... ORDER BY`），保持自增 ID 按时间顺序
- 所有表必须使用自增 `id BIGINT AUTO_INCREMENT PRIMARY KEY`，确保 InnoDB 物理存储按时间排序

### Excel 导出
- 单日期 / 多日期导出只做查询（`SELECT ... WHERE date BETWEEN ... ORDER BY`），不动数据库
- 清理数据库只有用户明确要求时才做

## 验证 SQL

```sql
SET @biz_date = '2026-05-01';

-- SYCM 服务核心监控：咨询人数已直接写入最终表
SELECT 日期, 咨询人数
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;

-- 飞猪订单：明细与店铺日度汇总是否一致落库
SELECT order_date, COUNT(*) AS 订单数, SUM(buy_mount) AS 件数合计, SUM(actual_fee) AS gmv明细合计
FROM Xiangwang.order_list
WHERE order_date = @biz_date
GROUP BY order_date;

SELECT 日期, total_bookings, total_pax, gmv
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;

-- SYCM 流量：PV/UV/流量来源/关注店铺人数
SELECT 日期, total_uv, total_pv, 流量来源广告_uv, 流量来源平台_uv
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;

SELECT 日期, 关注店铺人数
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;

-- 店铺每日登记：跨表规则后的完整数据（10个字段）
SELECT 日期, PV, UV, PaidUV, 关注店铺人数, GMV, 咨询人数, 下单买家数, 咨询转化率, 下单转化率
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;

-- 以下为已停用的赤兔 KPI 数据验证（保留供历史查询）
-- SELECT 'KPI-人均日接入' AS item, COUNT(*) AS rows_count
-- FROM Xiangwang.customer_service_data_daily
-- WHERE 日期 = @biz_date
-- UNION ALL
-- SELECT 'KPI-每周店铺个人数据', COUNT(*)
-- FROM Xiangwang.customer_service_performance_summary
-- WHERE date_time = @biz_date
-- UNION ALL
-- SELECT 'KPI-客服数据23年新', COUNT(*)
-- FROM Xiangwang.customer_service_performance_workload_analysis
-- WHERE date_time = @biz_date;

-- 以下为已停用的阿里妈妈数据验证（保留供历史查询）
-- SELECT '明星店铺' AS channel, date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
-- FROM Xiangwang.star_store
-- WHERE date_time = @biz_date
-- UNION ALL
-- SELECT '直通车', date_time, cost, imp, click, order_count, sales, ctr, cpc, NULL AS cpm, roi, cvr
-- FROM Xiangwang.tmall_express
-- WHERE date_time = @biz_date
-- UNION ALL
-- SELECT '引力魔方', date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
-- FROM Xiangwang.gravity_rubiks_cube
-- WHERE date_time = @biz_date
-- UNION ALL
-- SELECT '万相台', date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
-- FROM Xiangwang.wanxiangtai
-- WHERE date_time = @biz_date;
```

## 故障处理

- 某个业务失败时，先单独运行对应脚本复现。
- Chrome 未登录或页面过期时，复用统一调试窗口重新登录。
- 不要关闭共享 Chrome 调试会话；需要启动时使用 `bin/start-chrome-unified.sh`。
- 数据库连接失败时先检查 `.env`，当前本机优先使用 `HOST=localhost`。
- `sycm_service.sh` 中 jq 使用 `["中文key"]` 括号语法访问 JSON 中文字段，不可用 `.中文key` 点语法。

## 性能指标

### 当前版本（v5）

- **总耗时**：约 2.5-3.5 分钟（含度假订单导出轮询等待）
- **SYCM 服务核心监控**：约 5 秒（单 API 调用）
- **飞猪订单**：约 30 秒
- **新 GMV 采集**：约 30-60 秒（链路1 日历房分页 + 链路2 导出触发/轮询/下载/解析）
- **SYCM 流量**：约 20 秒
- **跨表规则**：<1 秒

### v4 → v5 改进

| 项目 | v4 | v5 |
|------|----|----|
| GMV 来源 | 飞猪订单 `actual_fee` 汇总 | 双链路（日历房 `checkOutRoomPrice` + 度假订单导出 `总金额`，排除付款时间空白） |
| GMV 采集脚本 | `fliggy_orders.sh` 内置 | `gmv_combined.sh` 独立脚本 |
| 数据源数量 | 3（SYCM服务+飞猪+SYCM流量） | 4（SYCM服务+飞猪+新GMV+SYCM流量） |

## 版本历史

- **v1** - 初始版本，3个业务，CDP导出Excel模式
- **v2** - 新增阿里妈妈投放日报、KPI改为API直读、新增数据库Excel导出技能、公共函数库、.env配置加载
- **v3** - 新增跨表规则应用脚本（8条规则），自动补齐 shop_daily_key_data 和 shop_data_daily_registration 的衍生字段；新增数据管理规范
- **v4** - 停用赤兔 KPI（客户未订购），咨询人数改为从 SYCM 服务核心监控 API 直接采集；新增 `sycm_service.sh` 和 `prepare_sycm_service_to_json.py`；更新执行流程、验证 SQL 和性能指标
- **v5** - GMV 改为双链路采集（链路1 日历房 `checkOutRoomPrice` + 链路2 度假订单导出 `总金额`，排除付款时间空白）；新增 `gmv_combined.sh`、`bin/prepare_gmv_combined_to_json.py`、`bin/prepare_gmv_combined_sql.py`；GMV 不再由 `fliggy_orders.sh` 计算

---

**技能名称**: openclaw-daily-data-collection
**技能版本**: v5
**最后更新**: 2026-06-10
**状态**: ✅ 生产就绪

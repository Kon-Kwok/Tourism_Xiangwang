---
name: openclaw-daily-data-collection
description: OpenClaw 侧调用飞猪业务四大日报采集。一键采集赤兔 KPI 客服报表、飞猪订单列表、SYCM 流量看板、阿里妈妈投放日报；当用户需要"日报数据""昨日日报""采集 x 日数据"或提及 KPI、订单、流量、阿里妈妈、直通车、万相台时使用。
---

# OpenClaw 每日数据采集技能

调用项目根目录的 `scripts/all.sh` 完成四大日报采集：赤兔 KPI 客服报表、飞猪订单列表、SYCM 流量看板、阿里妈妈投放日报。

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
./scripts/kpi_reports.sh 2026-05-01
./scripts/fliggy_orders.sh 2026-05-01
./scripts/sycm_flow.sh 2026-05-01
./scripts/alimama_daily.sh 2026-05-01
./scripts/apply_cross_table_rules.sh 2026-05-01
```

## 日期规则

- 日报采集必须固定为同一天：开始日期 = 结束日期 = `YYYY-MM-DD`。
- 用户说"5月1日日报"时，按当前年份解析为 `YYYY-05-01`；没有日期时执行昨天。
- 赤兔 KPI 三个报表都必须使用 `--date-mode day --date YYYY-MM-DD`，包括名字带"每周"的 `每周店铺个人数据` 和 `客服数据23年新`。
- KPI 下载文件名必须包含 `YYYY-MM-DD至YYYY-MM-DD`，否则视为错误数据，重新导出。

## 前置条件

- 使用统一 Chrome 调试窗口：`~/Tourism_Xiangwang/bin/start-chrome-unified.sh`
- Chrome 里已登录 `sycm.taobao.com`、`fsc.fliggy.com`、`kf.topchitu.com`、`brandsearch.taobao.com` / `one.alimama.com`
- 项目根目录 `.env` 已配置数据库连接，脚本会自动加载：

```bash
HOST=localhost
PORT=3306
USER=remote_user
PASS=your_mysql_password
```

## 目标表

| 业务 | 目标表 |
|---|---|
| 赤兔KPI客服报表 | `Xiangwang.customer_service_data_daily`、`Xiangwang.customer_service_performance_summary`、`Xiangwang.customer_service_performance_workload_analysis` |
| 飞猪订单列表 | `Xiangwang.order_list`、`Xiangwang.shop_daily_key_data` |
| SYCM流量看板 | `Xiangwang.shop_daily_key_data`、`Xiangwang.shop_data_daily_registration` |
| 阿里妈妈投放日报 | `Xiangwang.star_store`、`Xiangwang.tmall_express`、`Xiangwang.gravity_rubiks_cube`、`Xiangwang.wanxiangtai`、`Xiangwang.wanxiangtai_2` |

`Xiangwang.shop_daily_key_data` 的 `日期` 索引可能非唯一，写入必须保持 `UPDATE` 后 `INSERT ... WHERE NOT EXISTS`，不要改回 `ON DUPLICATE KEY UPDATE`。

## 关键口径

飞猪订单：

- 必须带 `--all-pages`。
- 订单明细进入 `Xiangwang.order_list`。
- 订单汇总必须先经过 `bin/prepare_order_list_for_storage.py`，再由 `bin/prepare_shop_daily_key_sql.py` 写入 `total_bookings`、`total_pax`、`gmv`。
- `gmv` 按 `actual_fee` 汇总；补差/尾款类订单只计入 `gmv`，不计入舱位和人数。

阿里妈妈投放：

- 明星店铺接口：`https://brandsearch.taobao.com/report/adrQuery/rptCampaignList2.json`
- one.alimama 场景接口：`https://one.alimama.com/report/query.json`
- 日期参数 `startTime/startdate = endTime/enddate = YYYY-MM-DD`。
- 固定口径：`effectConversionCycle/effectEqual = 3`，归因 `click`。
- 不给明星店铺接口传错误 `csrfID`。
- 入库时展示型字段按文本保存：`cost/sales/cpc/cpm/asp/cporder/cpshopping_cart/collection_cart_cost` 记为 `￥1,234.56`，`ctr/cvr/cart_rate/collection_cart_rate` 记为 `5.00%`；`roi` 和各类数量字段仍保留数值。

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

采集阶段各脚本只负责写入各自的基础表，跨表衍生字段由 `scripts/apply_cross_table_rules.sh` 统一补齐，共 8 条规则：

### 规则 1：阿里妈妈投放数据 → shop_daily_key_data
| 源表 | 目标字段 |
|------|----------|
| `star_store.cost/imp/click` | `pingxiaobao_cost/imp/click` |
| `tmall_express.cost/imp/click` | `tmall_express_cost/imp/click` |
| `gravity_rubiks_cube.cost/imp/click` | `gravity_rubiks_cube_cost/imp/click` |
| `wanxiangtai.cost/imp/click` | `mansa_dae_cost/views/click` |

注意：阿里妈妈表 cost 字段存储为 `￥1,234.56` 格式，写入 shop_daily_key_data 前须 `CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL)` 去除货币符号。

### 规则 2：KPI 询单人数汇总 → chat_volume
`customer_service_performance_summary` 所有客服 `询单人数` SUM → `shop_daily_key_data.chat_volume`

### 规则 3：四个渠道 booked_cabin 默认值 = 3
`pingxiaobao_booked_cabin` / `tmall_express_booked_cabin` / `gravity_rubiks_cube_booked_cabin` / `mansa_dae_booked_cabin` 均设为 3

### 规则 4：公式字段（shop_daily_key_data 内横向计算）
- `流量来源汇总` = `流量来源广告_uv` + `流量来源平台_uv`
- `直引万品点击量` = pingxiaobao_click + tmall_express_click + gravity_rubiks_cube_click + mansa_dae_click
- `cost_total` = pingxiaobao_cost + tmall_express_cost + gravity_rubiks_cube_cost + mansa_dae_cost
- `imp_total` = pingxiaobao_imp + tmall_express_imp + gravity_rubiks_cube_imp + mansa_dae_views
- `click_total` = pingxiaobao_click + tmall_express_click + gravity_rubiks_cube_click + mansa_dae_click

### 规则 5：shop_daily_key_data → shop_data_daily_registration
| 源字段 | 目标字段 |
|--------|----------|
| `total_pv` | `PV` |
| `total_uv` | `UV` |
| `gmv` | `GMV` |
| `流量来源汇总` | `PaidUV` |
| `total_bookings` | `下单买家数` |

### 规则 6：KPI 咨询人数汇总 → 店铺每日登记
`customer_service_performance_summary` 所有客服 `咨询人数` SUM → `shop_data_daily_registration.咨询人数`

### 规则 7：转化率公式（shop_data_daily_registration 内横向计算）
- `咨询转化率` = `下单买家数` / `咨询人数`
- `下单转化率` = `下单买家数` / `UV`

### 规则 8：super_recommendation_cost 暂无数据来源，暂时留空

## 执行流程

```
开始
  ↓
1. 赤兔KPI报表采集（3个报表）
   - API读取 → 转换JSON → 生成SQL → 入库
   ↓
2. 飞猪订单列表采集
   - HTTP采集（--all-pages）→ 预处理 → 订单明细入库 → 订单汇总入库
   ↓
3. SYCM流量看板采集
   - HTTP采集 → 转换SQL（含关注店铺人数）→ 入库
   ↓
4. 阿里妈妈投放日报采集
   - HTTP采集 → 数据转换 → 入库（5张表）
   ↓
5. 跨表规则应用（补齐衍生字段）
   - 8条规则：阿里妈妈数据 → shop_daily_key_data
   - KPI汇总 → chat_volume / 咨询人数
   - 公式计算：流量来源汇总、直引万品点击量、投放汇总
   - shop_daily_key_data → shop_data_daily_registration
   - 转化率计算
   ↓
完成（总耗时约3-4分钟）
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

-- 总览：四大业务目标表是否都有当日数据
SELECT 'KPI-人均日接入' AS item, COUNT(*) AS rows_count
FROM Xiangwang.customer_service_data_daily
WHERE 日期 = @biz_date
UNION ALL
SELECT 'KPI-每周店铺个人数据', COUNT(*)
FROM Xiangwang.customer_service_performance_summary
WHERE date_time = @biz_date
UNION ALL
SELECT 'KPI-客服数据23年新', COUNT(*)
FROM Xiangwang.customer_service_performance_workload_analysis
WHERE date_time = @biz_date
UNION ALL
SELECT '飞猪订单明细', COUNT(*)
FROM Xiangwang.order_list
WHERE order_date = @biz_date
UNION ALL
SELECT 'SYCM-店铺日度关键表', COUNT(*)
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date
UNION ALL
SELECT 'SYCM-关注店铺人数表', COUNT(*)
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date
UNION ALL
SELECT '阿里妈妈-明星店铺', COUNT(*)
FROM Xiangwang.star_store
WHERE date_time = @biz_date
UNION ALL
SELECT '阿里妈妈-直通车', COUNT(*)
FROM Xiangwang.tmall_express
WHERE date_time = @biz_date
UNION ALL
SELECT '阿里妈妈-引力魔方', COUNT(*)
FROM Xiangwang.gravity_rubiks_cube
WHERE date_time = @biz_date
UNION ALL
SELECT '阿里妈妈-万相台', COUNT(*)
FROM Xiangwang.wanxiangtai
WHERE date_time = @biz_date
UNION ALL
SELECT '阿里妈妈-万相台2', COUNT(*)
FROM Xiangwang.wanxiangtai_2
WHERE date_time = @biz_date;

-- KPI：客服三张表的核心指标
SELECT 日期, COUNT(*) AS 客服数, SUM(接待人数) AS 接待人数合计,
       ROUND(AVG(平均响应秒), 2) AS 平均响应秒
FROM Xiangwang.customer_service_data_daily
WHERE 日期 = @biz_date
GROUP BY 日期;

SELECT date_time, COUNT(*) AS 客服数, SUM(咨询人数) AS 咨询人数合计,
       SUM(接待人数) AS 接待人数合计, SUM(销售额) AS 销售额合计, SUM(订单数) AS 订单数合计
FROM Xiangwang.customer_service_performance_summary
WHERE date_time = @biz_date
GROUP BY date_time;

SELECT date_time, COUNT(*) AS 客服数, SUM(咨询人数) AS 咨询人数合计,
       SUM(接待人数) AS 接待人数合计, SUM(总消息) AS 总消息合计,
       ROUND(AVG(首次响应秒), 2) AS 平均首次响应秒
FROM Xiangwang.customer_service_performance_workload_analysis
WHERE date_time = @biz_date
GROUP BY date_time;

-- 飞猪订单：明细与店铺日度汇总是否一致落库
SELECT order_date, COUNT(*) AS 订单数, SUM(buy_mount) AS 件数合计, SUM(actual_fee) AS gmv明细合计
FROM Xiangwang.order_list
WHERE order_date = @biz_date
GROUP BY order_date;

SELECT 日期, total_bookings, total_pax, gmv
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;

-- SYCM：流量与关注店铺人数
SELECT 日期, total_uv, total_pv, 流量来源广告_uv, 流量来源平台_uv
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;

SELECT 日期, 关注店铺人数
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;

-- 阿里妈妈：四个主渠道核心字段
SELECT '明星店铺' AS channel, date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
FROM Xiangwang.star_store
WHERE date_time = @biz_date
UNION ALL
SELECT '直通车', date_time, cost, imp, click, order_count, sales, ctr, cpc, NULL AS cpm, roi, cvr
FROM Xiangwang.tmall_express
WHERE date_time = @biz_date
UNION ALL
SELECT '引力魔方', date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
FROM Xiangwang.gravity_rubiks_cube
WHERE date_time = @biz_date
UNION ALL
SELECT '万相台', date_time, cost, imp, click, order_count, sales, ctr, cpc, cpm, roi, cvr
FROM Xiangwang.wanxiangtai
WHERE date_time = @biz_date;

-- 阿里妈妈：万相台2分数据源明细，正常应含超级短视频/超级直播/货品运营/全站推广/小计
SELECT date_time, data_source, cost, imp, click, order_count, sales,
       shopping_cart, bookmark_product, collection_cart_count, ctr, cpc, cpm, roi, cvr
FROM Xiangwang.wanxiangtai_2
WHERE date_time = @biz_date
ORDER BY FIELD(data_source, '超级短视频', '超级直播', '货品运营', '全站推广', '小计'), data_source;

-- 店铺日度关键表：推广渠道汇总字段（含跨表规则计算后的衍生字段）
SELECT 日期,
       pingxiaobao_cost, pingxiaobao_imp, pingxiaobao_click,
       tmall_express_cost, tmall_express_imp, tmall_express_click,
       gravity_rubiks_cube_cost, gravity_rubiks_cube_imp, gravity_rubiks_cube_click,
       mansa_dae_cost, mansa_dae_views, mansa_dae_click,
       cost_total, imp_total, click_total,
       chat_volume, 流量来源汇总, 直引万品点击量
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;

-- 店铺每日登记：跨表规则后的完整数据
SELECT 日期, PV, UV, PaidUV, GMV, 咨询人数, 下单买家数, 咨询转化率, 下单转化率
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;
```

## 故障处理

- 某个业务失败时，先单独运行对应脚本复现。
- Chrome 未登录或页面过期时，复用统一调试窗口重新登录。
- 不要关闭共享 Chrome 调试会话；需要启动时使用 `bin/start-chrome-unified.sh`。
- 数据库连接失败时先检查 `.env`，当前本机优先使用 `HOST=localhost`。

## 性能指标

### 当前版本（v3）

- **总耗时**：约3-4分钟
- **KPI报表**：约2分钟（API直读，无需等待Excel下载）
- **飞猪订单**：约30秒
- **SYCM流量**：约20秒
- **阿里妈妈**：约30秒
- **跨表规则**：<1秒

### v2 → v3 改进

| 项目 | v2 | v3 |
|------|----|----|
| 衍生字段 | 缺失（24+8个NULL） | 自动补齐（8条规则） |
| shop_daily_key_data 完整度 | 6/30 字段 | 26/30 字段 |
| shop_data_daily_registration 完整度 | 1/9 字段 | 9/9 字段 |
| 新增脚本 | - | apply_cross_table_rules.sh |

## 版本历史

- **v1** - 初始版本，3个业务，CDP导出Excel模式
- **v2** - 新增阿里妈妈投放日报、KPI改为API直读、新增数据库Excel导出技能、公共函数库、.env配置加载
- **v3** - 新增跨表规则应用脚本（8条规则），自动补齐 shop_daily_key_data 和 shop_data_daily_registration 的衍生字段；新增数据管理规范

---

**技能名称**: openclaw-daily-data-collection
**技能版本**: v3
**最后更新**: 2026-05-18
**状态**: ✅ 生产就绪

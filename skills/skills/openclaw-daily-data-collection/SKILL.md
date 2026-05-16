---
name: openclaw-daily-data-collection
description: OpenClaw 侧调用飞猪业务四大日报采集。一键采集赤兔 KPI 客服报表、飞猪订单列表、SYCM 流量看板、阿里妈妈投放日报；当用户需要“日报数据”“昨日日报”“采集 x 日数据”或提及 KPI、订单、流量、阿里妈妈、直通车、万相台时使用。
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
```

## 日期规则

- 日报采集必须固定为同一天：开始日期 = 结束日期 = `YYYY-MM-DD`。
- 用户说“5月1日日报”时，按当前年份解析为 `YYYY-05-01`；没有日期时执行昨天。
- 赤兔 KPI 三个报表都必须使用 `--date-mode day --date YYYY-MM-DD`，包括名字带“每周”的 `每周店铺个人数据` 和 `客服数据23年新`。
- KPI 下载文件名必须包含 `YYYY-MM-DD至YYYY-MM-DD`。

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

-- 店铺日度关键表：推广渠道汇总字段
SELECT 日期,
       pingxiaobao_cost, pingxiaobao_imp, pingxiaobao_click,
       tmall_express_cost, tmall_express_imp, tmall_express_click,
       gravity_rubiks_cube_cost, gravity_rubiks_cube_imp, gravity_rubiks_cube_click,
       mansa_dae_cost, mansa_dae_views, mansa_dae_click,
       cost_total, imp_total, click_total
FROM Xiangwang.shop_daily_key_data
WHERE 日期 = @biz_date;
```

## 故障处理

- 某个业务失败时，先单独运行对应脚本复现。
- Chrome 未登录或页面过期时，复用统一调试窗口重新登录。
- 不要关闭共享 Chrome 调试会话；需要启动时使用 `bin/start-chrome-unified.sh`。
- 数据库连接失败时先检查 `.env`，当前本机优先使用 `HOST=localhost`。

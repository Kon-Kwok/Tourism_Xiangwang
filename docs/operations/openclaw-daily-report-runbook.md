# OpenClaw 日报采集代理 Runbook

本文档给 OpenClaw 代理使用，目标是稳定执行飞猪业务日报采集并完成入库校验。默认在仓库根目录 `/home/kk/Tourism_Xiangwang` 执行。

## 1. 固定目标

日报采集只做四件事：

1. 赤兔 KPI 三个报表入库到 `Xiangwang`。
2. 飞猪订单明细入库到 `Xiangwang.order_list`，订单汇总入库到 `Xiangwang.shop_daily_key_data`。
3. SYCM 流量看板入库到 `Xiangwang.shop_daily_key_data` 和 `Xiangwang.shop_data_daily_registration`。
4. 阿里妈妈投放日报入库到 `Xiangwang.star_store`、`Xiangwang.tmall_express`、`Xiangwang.gravity_rubiks_cube`、`Xiangwang.wanxiangtai`、`Xiangwang.wanxiangtai_2`。

日期必须是单日 `YYYY-MM-DD`。不要把“每周店铺个人数据”按周采集，所有 KPI 报表都必须使用同一天开始、同一天结束。

## 2. 前置检查

执行前确认 Chrome 调试会话存在：

```bash
ps aux | grep 'remote-debugging-port=9222' | grep -v grep
```

如果没有运行，从仓库根目录启动：

```bash
./bin/start-chrome-unified.sh
```

Chrome 中必须保持这些登录态：

- `kf.topchitu.com`：赤兔 KPI
- `fsc.fliggy.com`：飞猪商家工作台
- `sycm.taobao.com`：生意参谋
- `brandsearch.taobao.com` / `one.alimama.com`：阿里妈妈投放日报

数据库连接从项目根目录 `.env` 自动加载。当前推荐：

```bash
export HOST=localhost
export PORT=3306
export USER=remote_user
export PASS=<mysql_password>
export KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS=90
```

## 3. 一键采集命令

推荐只使用一键脚本，不要手动拆分，除非排查问题。

```bash
cd /home/kk/Tourism_Xiangwang
KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS=90 ./scripts/all.sh YYYY-MM-DD
```

示例：

```bash
KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS=90 ./scripts/all.sh 2026-04-24
```

成功标志：终端最后出现：

```text
✓ 所有业务采集完成！
```

KPI 下载文件名必须包含 `YYYY-MM-DD至YYYY-MM-DD`。如果文件名日期范围不对，本次 KPI 数据无效，需要重新导出。

## 4. 入库校验 SQL

采集完成后必须校验，不要只看脚本成功日志。

把下面的日期替换为目标日期：

```bash
DATE=YYYY-MM-DD
set -a && source .env && set +a
mysql -h ${HOST:-localhost} -P ${PORT:-3306} -u ${USER:-remote_user} -p${PASS} -N -e "
SELECT 日期,total_bookings,total_pax,gmv,total_uv,total_pv,流量来源广告_uv,流量来源平台_uv
FROM Xiangwang.shop_daily_key_data
WHERE 日期='${DATE}';

SELECT order_id,item_title,package_type,buy_mount,actual_fee,order_time,status_text
FROM Xiangwang.order_list
WHERE order_date='${DATE}'
ORDER BY order_time DESC;

SELECT 'daily', COUNT(*)
FROM Xiangwang.customer_service_data_daily
WHERE 日期='${DATE}';

SELECT 'summary', COUNT(*)
FROM Xiangwang.customer_service_performance_summary
WHERE date_time='${DATE}';

SELECT 'workload', COUNT(*)
FROM Xiangwang.customer_service_performance_workload_analysis
WHERE date_time='${DATE}';

SELECT 'registration', COUNT(*), MAX(关注店铺人数)
FROM Xiangwang.shop_data_daily_registration
WHERE 日期='${DATE}';

SELECT 'wanxiangtai_2', COUNT(*)
FROM Xiangwang.wanxiangtai_2
WHERE date_time='${DATE}';
"
```

校验标准：

- `shop_daily_key_data` 必须有目标日期记录。
- 三个 KPI 表行数必须大于 0。
- `registration` 第一列计数必须是 `1`。
- `wanxiangtai_2` 通常应有 5 行（4 个来源 + 小计）。
- 订单明细可以为 0，但如果有订单，`item_title` 应尽量有值。

## 5. 订单口径

订单采集必须使用 `--all-pages`。一键脚本已内置，不要改掉。

订单汇总规则：

- `gmv`：所有保留订单的 `actual_fee` 汇总。
- `total_pax`：按 `package_type` 中的 `N人房` 和“通兑”规则计算。
- `total_bookings`：按房型人数折算 booking。
- 如果 `item_title` 包含 `补差` 或 `尾款`，该订单只计入 `gmv`，不计入 `total_pax` 和 `total_bookings`。
- 状态为 `交易关闭`、`等待买家付款` 的订单不参与归一化后的明细和汇总。

注意：`fliggy_orders.sh` 当前日志里的“采集到 N 条订单”使用 `jq length` 统计 JSON 顶层字段，可能显示为 `2`，这不是实际订单数。实际订单数以数据库查询或 JSON 中 `rows` 长度为准。

## 6. 常见问题处理

### 登录失效

现象：订单接口返回登录页、KPI 页面找不到、SYCM 无数据。

处理：在 Chrome 调试窗口中重新登录对应网站，然后重跑同一天命令。

### KPI 下载等待超时

处理：

```bash
export KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS=180
```

重新执行一键脚本。确认下载目录里新文件日期范围为目标单日。

### 订单标题为空

正常邮轮订单标题来自 `itemInfo.itemTitle`，已入库到 `Xiangwang.order_list.item_title`。如果为空，优先检查原始接口是否缺少 `itemInfo.itemTitle`，不要把 `package_type` 当商品标题使用。

### 重跑同一天

允许重跑。当前订单明细先清理目标 `order_date` 再插入，日度关键数据按 `日期` 更新或插入。重跑后必须再次执行校验 SQL。

## 7. OpenClaw 输出格式

每次执行结束后，OpenClaw 应输出以下摘要：

```text
YYYY-MM-DD 日报采集完成
KPI: daily=<行数>, summary=<行数>, workload=<行数>
订单: 明细=<订单数>, total_bookings=<值>, total_pax=<值>, gmv=<值>
流量: total_uv=<值>, total_pv=<值>, 广告_uv=<值>, 平台_uv=<值>
关注店铺人数: <值>
阿里妈妈: wanxiangtai_2=<行数>
异常: 无 / <具体异常>
```

如果任一校验项为空或报错，不要输出“完成”，应输出失败原因和建议动作。

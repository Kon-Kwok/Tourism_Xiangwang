# 昨日日报入库 Skill 设计

## 目标

创建一个本地 Codex Skill，在用户说“帮我获取昨日日报数据”时，自动执行 `/home/kk/Tourism_YingXiang` 里昨日的 6 条顶层入库链路，并在失败时优先参考 `.learnings` 做修复和重试。

## 方案

采用 `Skill + bundled script`：

- Skill 负责触发条件、执行边界、排障顺序、`.learnings` 使用方式
- bundled script 负责固定生成“昨天”的 6 条命令、顺序执行、回查本地 MySQL、输出 JSON 结果

## 固定范围

昨日同一业务日期的 6 条链路：

1. 飞猪订单汇总 -> `Xiangwang.shop_daily_key_data`（`--all-pages` 采集后，经 `prepare_order_list_for_storage.py` 计算，再由 `prepare_shop_daily_key_sql.py` 写入）
2. SYCM 流量 -> `Xiangwang.shop_daily_key_data`
3. SYCM 关注店铺人数 -> `Xiangwang.shop_data_daily_registration`
4. `人均日接入` -> `Xiangwang.customer_service_data_daily`
5. `客服数据23年新` -> `Xiangwang.customer_service_performance_workload_analysis`
6. `每周店铺个人数据` -> `Xiangwang.customer_service_performance_summary`

## 成功标准

- 6 条命令都执行成功
- 每条命令后数据库回查通过
- Skill 输出昨日日期和每条链路的校验结果

## 失败处理

- 先读 `.learnings/LEARNINGS.md` 和 `.learnings/ERRORS.md`
- 优先套用已有失败经验
- 只修当前阻塞问题，先跑窄测试，再重跑 Skill 脚本
- 一旦当前真实执行成功，就停止，不为了“刷新经验”再额外重跑
- 只有这次真实执行中遇到的新失败模式，才追加到 `.learnings`

# 飞猪订单列表成交时间范围设计

## 背景

当前 `fliggy-order-list list` 只支持分页、业务类型和排序参数，不能按成交时间过滤。实际使用需要直接按“成交时间”区间拉取订单，同时在未显式传参时默认查询当天整天数据。

## 目标

在现有命令上增加成交时间范围参数：

```bash
python3 -m tourism_automation.cli.main fliggy-order-list list \
  --deal-start "2026-04-07 00:00:00" \
  --deal-end "2026-04-07 23:59:39"
```

当用户未传入时间参数时，默认使用本地当天：

- `deal_start`: 当天 `00:00:00`
- `deal_end`: 当天 `23:59:59`

## 范围

本次只扩展现有 `fliggy-order-list list` 命令和对应 HTTP 请求参数：

- 新增 CLI 参数 `--deal-start`
- 新增 CLI 参数 `--deal-end`
- 未传参时自动生成当天整天默认值
- 将成交时间范围写入订单列表接口请求
- 在输出结果中保留最终使用的时间范围，便于核对

本次不做：

- 新增独立 `--date` 参数
- 新增数据库存储
- 新增批量翻页导出
- 新增其他筛选维度

## 方案选择

采用方案 A：在现有 `fliggy-order-list list` 上直接新增 `--deal-start` 和 `--deal-end` 两个可选参数。

选择理由：

- 保持现有命令形式，已有调用方不需要调整子命令结构
- 能覆盖“默认今日”和“精确到秒的自定义区间”两种需求
- 改动面集中在 CLI 和请求层，风险最小

不采用的方案：

- 只加 `--date`：无法覆盖精确截止秒级时间
- 同时加 `--date` 和区间参数：当前收益不足，参数设计会变复杂

## 设计

### CLI

在 [src/tourism_automation/collectors/fliggy_order_list/cli.py](/home/kk/Tourism_YingXiang/src/tourism_automation/collectors/fliggy_order_list/cli.py) 的 `list` 子命令增加：

- `--deal-start`
- `--deal-end`

参数规则：

- 两个参数都是字符串，格式固定为 `YYYY-MM-DD HH:MM:SS`
- 两个参数都不传时，默认使用当天整天
- 只传其中一个时，另一个也自动按当天整天补齐
- CLI 层不做复杂时间换算，只负责把最终的开始/结束时间传给 collector

默认时间使用本地系统时间生成，和当前命令运行机器保持一致。

### Collector

在 [src/tourism_automation/collectors/fliggy_order_list/collector.py](/home/kk/Tourism_YingXiang/src/tourism_automation/collectors/fliggy_order_list/collector.py) 扩展 `collect_order_list()` 参数：

- `deal_start: str`
- `deal_end: str`

collector 只负责把参数透传给 client，并把请求参数交给 normalize。

### Client

在 [src/tourism_automation/collectors/fliggy_order_list/client.py](/home/kk/Tourism_YingXiang/src/tourism_automation/collectors/fliggy_order_list/client.py) 扩展 `fetch_order_list()`，把成交时间区间编码到订单列表接口请求中。

请求仍然保持 `multipart/form-data`。新增字段沿用当前接口的请求参数风格，使用成交时间范围字段承载开始和结束时间。

实现要求：

- 不改变现有 `_tb_token_` 读取逻辑
- 不影响现有分页和排序参数
- 如果接口返回中的 `requestParams` 缺失成交时间字段，仍在规范化输出里保留本次实际传入的时间

### Normalize

在 [src/tourism_automation/collectors/fliggy_order_list/normalize.py](/home/kk/Tourism_YingXiang/src/tourism_automation/collectors/fliggy_order_list/normalize.py) 增加输出字段：

- `summary.deal_start`
- `summary.deal_end`

同时在 `request_params` 中保留接口回显和调用参数，方便检查实际命中的时间条件。

## 数据流

1. CLI 解析 `--deal-start` / `--deal-end`
2. 若缺省，生成当天 `00:00:00` 和 `23:59:59`
3. collector 将成交时间区间传给 client
4. client 组装 HTTP 表单并请求订单列表接口
5. normalize 返回订单列表、分页信息和最终使用的成交时间范围

## 错误处理

- 时间参数格式错误时，CLI 应抛出明确错误
- 若开始时间晚于结束时间，应抛出明确错误
- 保留现有认证失败和非法 JSON 错误处理逻辑

## 测试

新增或更新以下测试：

- CLI 默认不传时间时，解析得到当天 `00:00:00` 和 `23:59:59`
- CLI 显式传入 `--deal-start` / `--deal-end` 时，参数正确透传
- client 请求中包含成交时间范围字段
- normalize 输出包含最终使用的成交时间范围

## 验证

实现完成后至少执行：

```bash
python3 -m unittest tests.cli.test_main
python3 -m unittest tests.collectors.test_fliggy_order_list
python3 -m tourism_automation.cli.main fliggy-order-list list --page-num 1 --page-size 5
python3 -m tourism_automation.cli.main fliggy-order-list list --page-num 1 --page-size 5 --deal-start "2026-04-07 00:00:00" --deal-end "2026-04-07 23:59:39"
```

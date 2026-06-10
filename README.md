# Tourism Xiangwang 店铺每日登记

本分支只对接当前任务：采集并补齐 `Xiangwang.shop_data_daily_registration`，再导出只包含“店铺每日登记”sheet 的 Excel。

## 目标结果

最终 Excel 只输出这些字段：

| 字段 | 来源/计算口径 |
| --- | --- |
| `日期` | 采集日期 |
| `PV` | 流量数据 |
| `UV` | 流量数据 |
| `PaidUV` | 广告流量 UV + 平台流量 UV |
| `关注店铺人数` | 流量数据 |
| `GMV` | 链路1（日历房 checkOutRoomPrice）+ 链路2（度假订单导出 总金额，排除付款时间空白） |
| `咨询人数` | SYCM 服务核心监控 API `cstUv1d` |
| `咨询转化率` | `下单买家数 / 咨询人数` |
| `下单买家数` | 订单数据 |
| `下单转化率` | `下单买家数 / UV` |

## 运行方式

所有命令都在项目根目录执行：

```bash
cd /Users/dc/Desktop/Tourism_Xiangwang
```

启动采集用 Chrome：

```bash
./bin/start-chrome-unified.sh
```

在 Chrome 中完成当前任务所需页面登录后，采集并入库：

```bash
./scripts/all.sh 2026-06-03
```

不传日期时默认采集昨天：

```bash
./scripts/all.sh
```

导出 Excel：

```bash
./.venv/bin/python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py --date 2026-06-03
```

数据库连接自动读取项目根目录 `.env`，无需在命令行传凭据。

## 数据库配置

项目根目录 `.env` 会被采集脚本自动读取：

```bash
HOST=127.0.0.1
PORT=3306
USER=<mysql_user>
PASS=<mysql_password>
DATABASE=Xiangwang
```

导出脚本也可以通过命令行参数覆盖数据库连接信息。

## 数据表

当前最终业务表：

| 表 | 作用 |
| --- | --- |
| `shop_data_daily_registration` | 店铺每日登记最终表，也是 Excel 默认唯一输出表 |

当前必要中间表：

| 表 | 作用 |
| --- | --- |
| `order_list` | 保存订单明细 |
| `shop_daily_key_data` | 汇总订单和流量数据，供最终表补齐字段 |

已停用表（赤兔 KPI、阿里妈妈投放，保留为注释）：

| 表 | 状态 |
| --- | --- |
| `customer_service_data_daily` | 🚫 赤兔 KPI-人均日接入 |
| `customer_service_performance_summary` | 🚫 赤兔 KPI-每周店铺个人数据 |
| `customer_service_performance_workload_analysis` | 🚫 赤兔 KPI-客服数据23年新 |
| `star_store` / `tmall_express` / `gravity_rubiks_cube` / `wanxiangtai` / `wanxiangtai_2` | 🚫 阿里妈妈投放日报 |

## 验证

采集完成后，可以用下面 SQL 验证最终表：

```sql
SET @biz_date = '2026-06-03';

SELECT
  日期,
  PV,
  UV,
  PaidUV,
  关注店铺人数,
  GMV,
  咨询人数,
  咨询转化率,
  下单买家数,
  下单转化率
FROM Xiangwang.shop_data_daily_registration
WHERE 日期 = @biz_date;
```

导出的 workbook 应只有一个 sheet：`店铺每日登记`。

## 项目结构

```text
src/tourism_automation/   # CLI、采集器和共享客户端
bin/                      # 数据转换和 Chrome 辅助脚本
scripts/                  # 店铺每日登记采集编排脚本
skills/skills/            # OpenClaw/Codex 技能和 Excel 导出脚本
docs/                     # 架构、采集器和运维文档
sql/Xiangwang/            # Xiangwang 建表 SQL
tests/                    # unittest 测试
exports/                  # Excel 导出文件
```

## 采集流程

`scripts/all.sh` 按顺序执行以下步骤：

| 步骤 | 脚本 | 采集内容 |
| --- | --- | --- |
| 1 | `sycm_service.sh` | 咨询人数（SYCM 服务核心监控 API → shop_data_daily_registration） |
| 2 | `fliggy_orders.sh` | 下单买家数（飞猪订单列表 → order_list / shop_daily_key_data） |
| 3 | `gmv_combined.sh` | GMV（链路1 日历房 + 链路2 度假订单导出 → shop_daily_key_data.gmv） |
| 4 | `sycm_flow.sh` | PV / UV / PaidUV / 关注店铺人数（SYCM 流量看板） |
| 5 | `apply_cross_table_rules.sh` | 跨表规则补齐最终表（流量汇总、字段复制、转化率计算） |

## 注意事项

- 订单采集必须覆盖全部分页，`scripts/fliggy_orders.sh` 已带 `--all-pages`。
- GMV 由 `gmv_combined.sh` 独立采集（双链路），不再从 `fliggy_orders.sh` 的 `actual_fee` 计算。
- 度假订单导出为 `.xls` 格式，依赖 `xlrd` 库解析；导出轮询最多 15 次（每次间隔 2 秒）。
- `shop_daily_key_data` 的 `日期` 索引可能非唯一，写入保持 `UPDATE` 后 `INSERT ... WHERE NOT EXISTS`。
- macOS/Linux `date` 兼容性已由 `scripts/lib/common.sh` 自动处理，无需额外配置 PATH。
- 不要提交 cookies、本地 Chrome profile、数据库 dump 或真实密钥。

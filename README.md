# Tourism Xiangwang 店铺每日登记采集

本分支当前只面向“店铺每日登记”需求：采集必要数据源，补齐 `Xiangwang.shop_data_daily_registration`，并导出只包含“店铺每日登记”sheet 的 Excel。赤兔 KPI、飞猪订单、SYCM 流量仍会作为登记表的数据来源执行。

## 当前流程

1. 赤兔 KPI：采集客服报表，当前用于汇总 `咨询人数`。
2. 飞猪订单：采集全部订单页，写入订单明细，并汇总 `GMV`、`下单买家数`。
3. SYCM 流量：采集 `PV`、`UV`、流量来源和 `关注店铺人数`。
4. 跨表规则：把中间表数据补齐到 `shop_data_daily_registration`，并计算 `咨询转化率`、`下单转化率`。
5. Excel 导出：默认只导出 `shop_data_daily_registration`。

## 主要入口

所有命令都在项目根目录执行：

```bash
cd /Users/dc/Desktop/Tourism_Xiangwang

# 启动统一 Chrome 调试窗口
./bin/start-chrome-unified.sh

# 采集并入库昨天的数据
PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH" ./scripts/all.sh

# 采集并入库指定日期的数据
PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH" ./scripts/all.sh 2026-06-01

# 导出指定日期的店铺每日登记 Excel
python3 skills/skills/openclaw-daily-database-excel/scripts/export_daily_database_excel.py \
  --date 2026-06-01 \
  --output exports/daily_database_2026-06-01_shop_registration.xlsx \
  --host 127.0.0.1 \
  --port 3306 \
  --user <mysql_user> \
  --password <mysql_password> \
  --database Xiangwang
```

macOS 自带 `date` 不支持 GNU `-d` 参数，采集命令前面的 `PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"` 用来优先使用 Homebrew coreutils。Linux 环境通常可以不加这段。


```

## 数据范围

| 阶段 | 当前作用 | 主要表 |
| --- | --- | --- |
| 赤兔 KPI | 提供登记表 `咨询人数` | `customer_service_performance_summary`，以及保留入库的 KPI 基础表 |
| 飞猪订单 | 提供登记表 `GMV`、`下单买家数` | `order_list`、`shop_daily_key_data` |
| SYCM 流量 | 提供登记表 `PV`、`UV`、`PaidUV`、`关注店铺人数` | `shop_daily_key_data`、`shop_data_daily_registration` |
| 跨表规则 | 补齐最终登记表字段和转化率 | `shop_data_daily_registration` |
| 阿里妈妈投放 | 当前停用，历史代码保留为注释 | `star_store`、`tmall_express`、`gravity_rubiks_cube`、`wanxiangtai`、`wanxiangtai_2` |

当前最终业务目标表是 `shop_data_daily_registration`。`shop_daily_key_data`、`order_list` 和 KPI 表仍是必要中间表，不作为当前 Excel 默认输出。

## 环境配置

项目根目录 `.env` 会被采集脚本自动读取：

```bash
HOST=127.0.0.1
PORT=3306
USER=<mysql_user>
PASS=<mysql_password>
DATABASE=Xiangwang
```

浏览器采集依赖统一 Chrome 调试会话，端口 `9222`。采集前确认 Chrome 已登录：

- `sycm.taobao.com`
- `fsc.fliggy.com`
- `kf.topchitu.com`


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

## 开发命令

```bash
python3 -m unittest discover tests
python3 -m unittest tests.cli.test_main
python3 -m unittest tests.test_refactored_clients
```

## 注意事项

- 飞猪订单采集必须使用 `--all-pages`，`scripts/fliggy_orders.sh` 已带该参数。
- `shop_daily_key_data` 的 `日期` 索引可能非唯一，写入保持 `UPDATE` 后 `INSERT ... WHERE NOT EXISTS`。
- 不要提交 cookies、本地 Chrome profile、数据库 dump 或真实密钥。

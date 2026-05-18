# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

飞猪/千牛电商数据自动化采集系统，通过复用本机 Chrome 登录态自动采集网页数据并存储到 MySQL 数据库的 `Xiangwang` 统一 schema。

**核心特性**:
- 复用本机 Chrome 登录态
- 模块化容错设计
- 统一CLI命令入口
- 按场景使用 HTTP + Cookie 或 CDP + fetch

## 系统配置

### 密码信息
- **sudo密码**: `1`
- **MySQL连接方式**: 

主机地址: 172.28.190.60  (WSL当前IP)
端口: 3306
用户名: remote_user
密码: Tourism2024

### 数据库连接
```bash
# 连接到MySQL
sudo mysql

# 连接到统一业务数据库
sudo mysql Xiangwang
```

### 数据库口径补充
- 所有日报链路写入 `Xiangwang`，目标表以 `sql/Xiangwang/Xiangwang.sql` 为准。
- `Xiangwang.shop_daily_key_data` 这种按日期汇总多来源数据的表，当前脚本使用 `UPDATE` 后接 `INSERT ... WHERE NOT EXISTS` 合并同日数据，因为线上 `日期` 可能只是普通索引。只有确认 `日期` 已有唯一键时，才能改回 `ON DUPLICATE KEY UPDATE`。

## 核心架构

### 代码组织

主代码位于 `src/tourism_automation/`:

```
src/tourism_automation/
├── cli/                    # 统一命令行入口
├── collectors/             # 数据采集器
│   ├── sycm/              # 生意参谋采集器
│   ├── fliggy_home/       # 飞猪商家工作台首页采集器
│   └── fliggy_kpi/        # 飞猪客服与店铺KPI采集器
└── shared/                # 共享组件
    ├── chrome/            # Chrome登录态读取
    ├── http/              # HTTP客户端
    ├── cdp_client.py      # 统一CDP能力
    └── result/            # 模块化结果汇总
```

### 关键设计模式

1. **CLI统一入口**: 所有采集器通过 `python3 -m tourism_automation.cli.main` 调用
2. **Collector模式**: 每个采集器包含 `collector.py`, `client.py`, `normalize.py`, `storage.py`
3. **Chrome会话复用**: 统一复用 `9222` 调试 Chrome 登录态
4. **双轨采集**: 常规页面走 HTTP + Cookie，KPI 等场景走 CDP + fetch

## 常用命令

### Chrome调试窗口管理

```bash
# 启动Chrome调试窗口
./bin/start-chrome-unified.sh

# 检查Chrome调试窗口状态
ps aux | grep "remote-debugging-port=9222"

# 检查Chrome调试端口
curl -s http://localhost:9222/json/version

# 查看Chrome标签页
curl -s http://localhost:9222/json | jq '.[] | {id, url, title}'

# 查看Chrome日志
tail -f /tmp/chrome_debug.log

# ⚠️ 不要使用这些命令：
# pkill chrome  # 禁止！
# pkill -9 chrome  # 禁止！
```

### 数据采集

```bash
# 生意参谋 - 健康检查
python3 -m tourism_automation.cli.main sycm healthcheck

# 生意参谋 - 采集首页数据
python3 -m tourism_automation.cli.main sycm collect-home --date 2026-04-19 --shop-name "皇家加勒比国际游轮旗舰店"

# 生意参谋 - 列出所有可用页面
python3 -m tourism_automation.cli.main sycm list-pages

# 生意参谋 - 采集指定页面数据
python3 -m tourism_automation.cli.main sycm collect-page --page-id flow_monitor --date-range "2026-04-19|2026-04-19"

# 飞猪商家工作台 - 采集首页数据
python3 -m tourism_automation.cli.main fliggy-home collect-home --date 2026-04-19 --shop-name "皇家加勒比国际游轮旗舰店"

# 飞猪客服KPI - 采集员工KPI数据
python3 -m tourism_automation.cli.main fliggy-kpi employee --date 2026-04-19 --method api --shop-name "皇家加勒比国际游轮旗舰店"
```

### 测试

```bash
# 运行所有测试
python3 -m unittest discover tests

# 运行特定测试
python3 -m unittest tests.cli.test_main
python3 -m unittest tests.collectors.test_sycm
python3 -m unittest tests.collectors.test_fliggy_home
python3 -m unittest tests.test_refactored_clients
```

### 数据库操作

#### 建表和初始化

```bash
# 一键创建所有数据库和表
./bin/setup_database.sh

# 或使用Python脚本
python3 bin/setup_database.py
```

#### 数据查看

```bash
# 查看采集批次记录
sudo mysql Xiangwang -e "SELECT * FROM collection_batches ORDER BY started_at DESC LIMIT 10;"

# 查看采集的指标数据
sudo mysql Xiangwang -e "SELECT * FROM homepage_metrics WHERE biz_date = '2026-04-19';"

# 查看飞猪客服日数据
sudo mysql Xiangwang -e "SELECT * FROM customer_service_data_daily WHERE 日期 = '2026-04-24';"

# 查看飞猪客服绩效汇总
sudo mysql Xiangwang -e "SELECT * FROM customer_service_performance_summary WHERE date_time = '2026-04-24';"

# 查看飞猪客服工作量分析
sudo mysql Xiangwang -e "SELECT * FROM customer_service_performance_workload_analysis WHERE date_time = '2026-04-24';"
```

### 赤兔KPI三个报表完整流程

系统支持从赤兔名品KPI系统下载3个报表，转换为JSON，然后入库：

#### 1. 人均日接入报表

```bash
# 步骤1: 使用CDP导出Excel
python3 -m tourism_automation.cli.main shop-kpi-export \
  --report-name "人均日接入" \
  --date-mode day \
  --date 2026-04-24

# 步骤2: Excel转换为JSON
python3 bin/prepare_shop_kpi_excel_to_json.py \
  ~/Downloads/自定义报表_人均日接入*.xlsx > result/kpi1_人均日接入.json

# 步骤3: JSON转换为SQL并入库
cat result/kpi1_人均日接入.json | \
  python3 bin/prepare_customer_service_data_daily_sql.py | \
  sudo mysql Xiangwang
```

**对应表**: `Xiangwang.customer_service_data_daily`
**数据脚本**: `bin/prepare_customer_service_data_daily_sql.py`

#### 2. 每周店铺个人数据报表

```bash
# 步骤1: 使用CDP导出Excel
python3 -m tourism_automation.cli.main shop-kpi-export \
  --report-name "每周店铺个人数据" \
  --date-mode day \
  --date 2026-04-24

# 步骤2: Excel转换为JSON
python3 bin/prepare_shop_kpi_excel_to_json.py \
  ~/Downloads/自定义报表_每周店铺个人数据*.xlsx > result/kpi2_每周店铺个人数据.json

# 步骤3: JSON转换为SQL并入库
cat result/kpi2_每周店铺个人数据.json | \
  python3 bin/prepare_customer_service_performance_summary_sql.py | \
  sudo mysql Xiangwang
```

**对应表**: `Xiangwang.customer_service_performance_summary`
**数据脚本**: `bin/prepare_customer_service_performance_summary_sql.py`

#### 3. 客服数据23年新报表

```bash
# 步骤1: 使用CDP导出Excel
python3 -m tourism_automation.cli.main shop-kpi-export \
  --report-name "客服数据23年新" \
  --date-mode day \
  --date 2026-04-24

# 步骤2: Excel转换为JSON
python3 bin/prepare_shop_kpi_excel_to_json.py \
  ~/Downloads/自定义报表_客服数据23年新*.xlsx > result/kpi3_客服数据23年新.json

# 步骤3: JSON转换为SQL并入库
cat result/kpi3_客服数据23年新.json | \
  python3 bin/prepare_customer_service_performance_workload_sql.py | \
  sudo mysql Xiangwang
```

**对应表**: `Xiangwang.customer_service_performance_workload_analysis`
**数据脚本**: `bin/prepare_customer_service_performance_workload_sql.py`

#### 批量导出脚本

```bash
# 使用批量导出脚本一次性下载所有3个报表
./bin/download_all_kpi_reports.sh

# 然后手动转换和入库每个报表
```

### 飞猪订单列表数据入库

飞猪订单列表采集后需要经过预处理才能入库。日报链路必须使用 `--all-pages`，否则 `total_bookings`、`total_pax`、`gmv` 只会按第一页订单计算。

```bash
# 步骤1: 采集订单列表
python3 -m tourism_automation.cli.main fliggy-order-list list \
  --page-num 1 --page-size 100 --all-pages \
  --deal-start "2026-04-24 00:00:00" \
  --deal-end "2026-04-24 23:59:59" > result/orders_raw.json

# 步骤2: 数据预处理
cat result/orders_raw.json | \
  python3 bin/prepare_order_list_for_storage.py > result/orders_prepared.json

# 步骤3: 订单明细入库
cat result/orders_prepared.json | \
  python3 bin/prepare_order_list_sql.py | \
  mysql Xiangwang

# 步骤4: 订单汇总入库店铺日度关键表
cat result/orders_prepared.json | \
  python3 bin/prepare_shop_daily_key_sql.py | \
  mysql Xiangwang
```

### 生意参谋数据入库

生意参谋数据通过自动采集直接入库，无需手动转换：

```bash
# 首页指标数据自动入库
python3 -m tourism_automation.cli.main sycm collect-home \
  --date 2026-04-24 \
  --shop-name "皇家加勒比国际游轮旗舰店"

# 数据自动存储到 Xiangwang.homepage_metrics 等表
```

**对应表**: `Xiangwang.homepage_metrics`, `Xiangwang.homepage_trends` 等

### 店铺日度数据入库

统一数据库包含手动登记数据，也包含日报自动采集写入的日度关键数据：

#### 1. 店铺数据每日登记

```bash
# 假设已有SYCM流量JSON，统一转换为SQL后处理

cat shop_data_daily.json | \
  python3 bin/prepare_sycm_flow_sql.py | \
  sudo mysql Xiangwang
```

**对应表**: `Xiangwang.shop_data_daily_registration`

#### 2. 飞猪店铺日度关键数据

```bash
# 包含订单汇总等多来源数据汇总
# 对应脚本: bin/prepare_shop_daily_key_sql.py

cat orders_prepared.json | \
  python3 bin/prepare_shop_daily_key_sql.py | \
  sudo mysql Xiangwang
```

**对应表**: `Xiangwang.shop_daily_key_data`

**重要说明**：
- 该表按日期汇总多来源数据
- 当前脚本使用 `UPDATE` 后接 `INSERT ... WHERE NOT EXISTS`，适配 `日期` 不是唯一键的线上表
- 如果后续改成 `ON DUPLICATE KEY UPDATE`，必须先确认 `日期` 字段具备唯一键

## 数据库结构

### 统一数据库表

- `collection_batches`: 生意参谋采集批次记录
- `homepage_metrics`: 生意参谋首页核心指标
- `homepage_trends`: 生意参谋首页趋势序列
- `customer_service_data_daily`: 客服数据汇总-日数据
- `customer_service_data_weekly`: 客服数据汇总-周数据
- `customer_service_performance_summary`: 客服绩效-汇总
- `customer_service_performance_workload_analysis`: 客服绩效-工作量分析
- `order_list`: 飞猪订单列表
- `shop_daily_key_data`: 店铺日度关键数据
- `shop_data_daily_registration`: 店铺数据每日登记
- `star_store`: 明星店铺
- `tmall_express`: 直通车
- `gravity_rubiks_cube`: 引力魔方
- `wanxiangtai`: 万相台
- `wanxiangtai_2`: 万相台2

详细表结构参见 `sql/` 目录下的SQL文件。

## 开发注意事项

### 添加新采集器

1. 在 `src/tourism_automation/collectors/` 创建新目录
2. 实现标准文件结构:
   - `collector.py`: 采集器主逻辑
   - `client.py`: API客户端
   - `normalize.py`: 数据规范化
   - `storage.py`: 数据库存储
   - `cli.py`: CLI命令注册
3. 在 `src/tourism_automation/cli/main.py` 中注册新的subparser

### Chrome会话管理

**⚠️ 重要规则：禁止关闭Chrome调试窗口！**

**Chrome调试窗口配置**：
- 调试端口：`9222`
- 配置目录：`~/.config/google-chrome-debug`
- Cookie路径：`~/.config/google-chrome-debug/Default/Cookies`
- 启动脚本：`bin/start-chrome-unified.sh`

**为什么不能关闭**：
- Chrome调试窗口用于所有数据采集
- 关闭后需要重新登录所有网站
- 可能需要再次输入验证码
- 破坏已建立的登录会话

**正确使用方式**：
1. Chrome调试窗口应该**一直运行**，不要关闭
2. 可以最小化窗口，但不关闭
3. 检查状态：`ps aux | grep "remote-debugging-port=9222"`
4. 如果意外停止，运行：`./bin/start-chrome-unified.sh`

**Chrome识别特征**：
```bash
# 调试Chrome，禁止关闭
chrome --remote-debugging-port=9222 --user-data-dir=/home/kk/.config/google-chrome-debug

# 正常Chrome，可以关闭
chrome --user-data-dir=/home/kk/.config/google-chrome
```

**禁止的操作**：
- ❌ 不要运行 `pkill chrome`
- ❌ 不要关闭Chrome调试窗口
- ❌ 不要删除 `~/.config/google-chrome-debug` 目录
- ❌ 不要在Chrome中点击"退出登录"

**Chrome会话管理技术细节**：
- 使用 `secretstorage` 读取Chrome加密密钥
- CDP脚本使用环境变量 `CDP_PORT_FILE` 定位调试端口
- 仅读取Cookie，不使用CDP进行页面操作

### 数据库Schema

- 所有自动采集表都需要 `batch_id` 字段用于追溯
- 使用 utf8mb4 字符集支持中文
- 日期字段使用 DATE 类型
- 金额字段使用 DECIMAL 类型保证精度

### 依赖管理

项目主要依赖:
- `requests`: HTTP客户端
- `pymysql`: MySQL连接
- `secretstorage`: Chrome密钥读取
- `cryptography`: Cookie解密
- `openpyxl`: Excel文件处理

## 数据处理完整流程

### 数据获取方式分类

1. **自动采集**：直接入库，无需手动处理
   - 生意参谋首页指标
   - 飞猪商家工作台首页数据
   - 飞猪客服KPI
   - 飞猪订单列表

2. **半自动采集**：需要导出Excel后转换入库
   - 赤兔KPI三个报表

### 核心脚本说明

#### Excel转JSON脚本

**`bin/prepare_shop_kpi_excel_to_json.py`**
- 功能：将赤兔KPI导出的Excel文件转换为统一JSON格式
- 输入：Excel文件路径
- 输出：JSON格式
- 使用：`python3 bin/prepare_shop_kpi_excel_to_json.py <excel_file>`

#### JSON转SQL脚本

**赤兔KPI三个报表对应三个SQL生成脚本**：

1. **`bin/prepare_customer_service_data_daily_sql.py`**
   - 报表：人均日接入
   - 目标表：`Xiangwang.customer_service_data_daily`
   - 字段：日期、旺旺、接待人数、平均响应秒、回复率等

2. **`bin/prepare_customer_service_performance_summary_sql.py`**
   - 报表：每周店铺个人数据
   - 目标表：`Xiangwang.customer_service_performance_summary`
   - 字段：旺旺昵称、咨询人数、接待人数、询单人数、销售额等

3. **`bin/prepare_customer_service_performance_workload_sql.py`**
   - 报表：客服数据23年新
   - 目标表：`Xiangwang.customer_service_performance_workload_analysis`
   - 字段：旺旺昵称、咨询人数、接待人数、直接/转入/转出人数、消息数等

**其他数据处理脚本**：

- **`bin/prepare_order_list_for_storage.py`**：飞猪订单列表数据预处理
- **`bin/prepare_shop_daily_key_sql.py`**：千牛店铺日度关键数据SQL生成
- **`bin/prepare_sycm_flow_sql.py`**：SYCM流量和关注店铺人数SQL生成

### 数据入库标准流程

#### PipeLine模式

```bash
# 完整的数据处理Pipeline：Excel -> JSON -> SQL -> Database
python3 bin/prepare_shop_kpi_excel_to_json.py ~/Downloads/报表.xlsx | \
  python3 bin/prepare_customer_service_data_daily_sql.py | \
  sudo mysql Xiangwang
```

#### 分步模式

```bash
# 步骤1: Excel转JSON
python3 bin/prepare_shop_kpi_excel_to_json.py ~/Downloads/报表.xlsx > temp.json

# 步骤2: 检查JSON格式
cat temp.json | jq .summary

# 步骤3: JSON转SQL
cat temp.json | python3 bin/prepare_customer_service_data_daily_sql.py > temp.sql

# 步骤4: 检查SQL
cat temp.sql

# 步骤5: 执行SQL
sudo mysql Xiangwang < temp.sql
```

### 数据验证

#### 验证数据是否成功入库

```bash
# 验证赤兔KPI数据
sudo mysql Xiangwang -e "
  SELECT 
    '人均日接入' as 报表类型, 
    COUNT(*) as 记录数, 
    MAX(日期) as 最新日期 
  FROM customer_service_data_daily
  UNION ALL
  SELECT 
    '每周店铺个人数据', 
    COUNT(*), 
    MAX(date_time) 
  FROM customer_service_performance_summary
  UNION ALL
  SELECT 
    '客服数据23年新', 
    COUNT(*), 
    MAX(date_time) 
  FROM customer_service_performance_workload_analysis;
"

# 验证飞猪订单数据
sudo mysql Xiangwang -e "
  SELECT 
    COUNT(*) as 订单数, 
    COUNT(DISTINCT DATE(order_time)) as 覆盖天数,
    MIN(order_time) as 最早订单,
    MAX(order_time) as 最新订单
  FROM order_list;
"
```

### 错误处理

#### 常见错误及解决方案

1. **Excel文件未找到**
   - 检查下载路径：`ls -lt ~/Downloads/*.xlsx`
   - 确认文件名格式：`自定义报表_*_*.xlsx`

2. **JSON格式错误**
   - 使用 `jq` 验证：`cat temp.json | jq .`
   - 检查 `summary.report_name` 字段是否正确

3. **SQL执行失败**
   - 检查表是否存在：`sudo mysql Xiangwang -e "SHOW TABLES;"`
   - 检查字段是否匹配：查看 `sql/` 目录下的建表SQL

4. **字符编码问题**
   - 确保数据库使用 utf8mb4 字符集
   - 检查SQL文件的编码格式

## 快速参考：数据源与脚本映射表

| 数据源 | 采集方式 | Excel转JSON | JSON转SQL | 目标数据库 | 目标表 |
|--------|----------|-------------|-----------|------------|--------|
| **赤兔KPI - 人均日接入** | CDP自动导出 | `prepare_shop_kpi_excel_to_json.py` | `prepare_customer_service_data_daily_sql.py` | Xiangwang | customer_service_data_daily |
| **赤兔KPI - 每周店铺个人数据** | CDP自动导出 | `prepare_shop_kpi_excel_to_json.py` | `prepare_customer_service_performance_summary_sql.py` | Xiangwang | customer_service_performance_summary |
| **赤兔KPI - 客服数据23年新** | CDP自动导出 | `prepare_shop_kpi_excel_to_json.py` | `prepare_customer_service_performance_workload_sql.py` | Xiangwang | customer_service_performance_workload_analysis |
| **飞猪订单列表** | HTTP自动采集 | N/A | `prepare_order_list_for_storage.py` + `prepare_order_list_sql.py` | Xiangwang | order_list |
| **飞猪订单汇总** | HTTP自动采集 | N/A | `prepare_order_list_for_storage.py` + `prepare_shop_daily_key_sql.py` | Xiangwang | shop_daily_key_data |
| **生意参谋首页** | HTTP自动采集 | N/A | 自动入库 | Xiangwang | homepage_metrics |
| **生意参谋流量** | HTTP自动采集 | N/A | `prepare_sycm_flow_sql.py` | Xiangwang | shop_daily_key_data |
| **飞猪商家工作台** | HTTP自动采集 | N/A | 自动入库 | Xiangwang | 多个业务模块表 |
| **飞猪客服KPI** | API自动采集 | N/A | 自动入库 | Xiangwang | employee_kpi_metrics |
| **店铺每日登记** | 流量链路更新关注人数 | 自定义 | `prepare_sycm_flow_sql.py` | Xiangwang | shop_data_daily_registration |

## 一键批量采集脚本示例

创建 `bin/daily_collection.sh` 用于日常批量采集：

```bash
#!/bin/bash
DATE=${1:-$(date -d "yesterday" +%Y-%m-%d)}
SHOP="皇家加勒比国际游轮旗舰店"

echo "开始采集 $DATE 的数据..."

# 1. 生意参谋首页
python3 -m tourism_automation.cli.main sycm collect-home --date $DATE --shop-name "$SHOP"

# 2. 生意参谋流量
python3 -m tourism_automation.cli.main sycm flow-monitor --date $DATE --shop-name "$SHOP"

# 3. 飞猪商家工作台
python3 -m tourism_automation.cli.main fliggy-home collect-home --date $DATE --shop-name "$SHOP"

# 4. 飞猪客服KPI
python3 -m tourism_automation.cli.main fliggy-kpi employee --date $DATE --method api --shop-name "$SHOP"

# 5. 飞猪订单列表
python3 -m tourism_automation.cli.main fliggy-order-list list \
  --page-num 1 --page-size 100 --all-pages \
  --deal-start "${DATE} 00:00:00" \
  --deal-end "${DATE} 23:59:59" > result/orders_raw_${DATE}.json

python3 bin/prepare_order_list_for_storage.py < result/orders_raw_${DATE}.json > result/orders_${DATE}.json
python3 bin/prepare_order_list_sql.py < result/orders_${DATE}.json | mysql Xiangwang
python3 bin/prepare_shop_daily_key_sql.py < result/orders_${DATE}.json | mysql Xiangwang

# 6. 赤兔KPI三个报表
echo "请手动导出赤兔KPI三个报表，然后运行："
echo "./bin/import_kpi_reports.sh"

echo "采集完成！"
```

使用方法：
```bash
chmod +x bin/daily_collection.sh
./bin/daily_collection.sh 2026-04-24
```

### 文档目录

- `docs/README.md`: 文档总入口
- `docs/architecture/`: 架构文档
- `docs/collectors/`: 采集器文档
- `docs/implementation/`: 实现背景与设计说明
- `sql/`: 建表SQL和Excel数据

# bin目录脚本说明

## 核心脚本（必需）

### Chrome启动与保活（2个）
- **start-chrome-unified.sh** - 统一Chrome调试窗口启动脚本
  - 端口：9222
  - 配置目录：`~/.config/google-chrome-debug`
  - 用途：所有数据采集的前置条件

- **refresh_chrome_tabs.py** - 业务标签页自动刷新守护脚本
  - 调用方式：由 `start-chrome-unified.sh` 自动拉起
  - 默认间隔：30分钟
  - 用途：保持 SYCM、飞猪、赤兔、阿里妈妈等页面 Cookie 活跃

### KPI页面准备（1个）
- **ensure_topchitu_custom_report.py**
  - 功能：确保赤兔自定义 KPI 页面已打开到指定报表
  - 调用方式：由 `scripts/kpi_reports.sh` 自动调用

### 数据转换流程（8个）

#### Excel转JSON
- **prepare_shop_kpi_excel_to_json.py**
  - 功能：将赤兔KPI导出的Excel转换为统一JSON格式
  - 输入：Excel文件路径
  - 输出：JSON（summary + rows）

#### 赤兔KPI转SQL（3个报表）
1. **prepare_customer_service_data_daily_sql.py**
   - 报表：人均日接入（id=1721）
   - 目标表：`Xiangwang.customer_service_data_daily`

2. **prepare_customer_service_performance_summary_sql.py**
   - 报表：每周店铺个人数据（id=1996）
   - 目标表：`Xiangwang.customer_service_performance_summary`

3. **prepare_customer_service_performance_workload_sql.py**
   - 报表：客服数据23年新（id=2496）
   - 目标表：`Xiangwang.customer_service_performance_workload_analysis`

#### 飞猪订单处理（3个）
- **prepare_order_list_for_storage.py**
  - 功能：订单数据预处理（按“通兑”和“N人房”规则计算 `total_booking`、`total_pax`，并汇总 `gmv`）
  
- **prepare_order_list_sql.py**
  - 功能：将订单JSON转换为SQL
  - 目标表：`Xiangwang.order_list`

- **prepare_shop_daily_key_sql.py**
  - 功能：将订单预处理后的汇总指标转换为SQL
  - 目标表：`Xiangwang.shop_daily_key_data`
  - 字段：`total_bookings`、`total_pax`、`gmv`

#### SYCM流量（1个）
- **prepare_sycm_flow_sql.py**
  - 功能：将SYCM流量JSON转换为SQL
  - 目标表：`Xiangwang.shop_daily_key_data`、`Xiangwang.shop_data_daily_registration`

### 数据库初始化（1个）
- **setup_database.py**
  - 功能：创建数据库和表结构
  - 用途：首次部署或需要重建表结构时使用

---

## 脚本使用流程

### 业务1：赤兔KPI三个报表

```bash
# 步骤1：导出Excel
python3 -m tourism_automation.cli.main shop-kpi-export --report-name "人均日接入" --date-mode day --date 2026-04-24

# 步骤2：等待下载
sleep 10

# 步骤3：转换和入库
EXCEL=$(ls -t ~/Downloads/自定义报表*2026-04-24至2026-04-24.xlsx | head -1)
python3 bin/prepare_shop_kpi_excel_to_json.py "$EXCEL" | \
  python3 bin/prepare_customer_service_data_daily_sql.py | \
  mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" Xiangwang
```

### 业务2：飞猪订单列表

```bash
python3 -m tourism_automation.cli.main fliggy-order-list list \
  --page-num 1 --page-size 100 --all-pages \
  --deal-start "2026-04-24 00:00:00" \
  --deal-end "2026-04-24 23:59:59" > /tmp/orders_raw.json

python3 bin/prepare_order_list_for_storage.py < /tmp/orders_raw.json > /tmp/orders_prep.json

python3 bin/prepare_order_list_sql.py < /tmp/orders_prep.json | \
  mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" Xiangwang

python3 bin/prepare_shop_daily_key_sql.py < /tmp/orders_prep.json | \
  mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" Xiangwang
```

### 业务3：SYCM流量看板

```bash
python3 -m tourism_automation.cli.main sycm flow-monitor \
  --date 2026-04-24 --shop-name "皇家加勒比国际游轮旗舰店" | \
  python3 bin/prepare_sycm_flow_sql.py | \
  mysql -h "$HOST" -P "$PORT" -u "$USER" -p"$PASS" Xiangwang
```

---

## 已删除的冗余脚本

### Chrome相关（5个）
- ensure-chrome-debug.sh
- setup-chrome-cdp.sh
- start-chrome-for-kpi.sh
- start-chrome-isolated.sh
- start-chrome-with-debug.sh

**原因**：已被 `start-chrome-unified.sh` 统一取代

### 测试/临时脚本（3个）
- compare_alimama_excel_http.py
- test_kpi_reports.sh
- test_mysql_connection.py

**原因**：临时测试脚本，不是日常使用

### 一次性配置工具（4个）
- exec_mysql_sql.py
- import-windows-cookies.py
- open-websites.py
- setup_database.sh

**原因**：一次性初始化工具，不是日常操作

### 店铺数据辅助脚本（2个）
- prepare_shop_daily_key_flow_monitor_sql.py
- prepare_shop_data_daily_registration_sql.py

**原因**：主流程使用 `prepare_sycm_flow_sql.py` 一次性写入流量和关注店铺人数，不再保留拆分入口。

### 批量脚本（1个）
- download_all_kpi_reports.sh

**原因**：临时批量脚本，应该使用主循环

---

## 设计原则

保留脚本遵循以下原则：

1. **单一职责**：每个脚本只做一件事
2. **Pipeline友好**：支持管道连接（`|`）
3. **幂等性**：可重复执行，不会重复插入数据
4. **必要性**：删除后无法通过其他方式实现的功能

---

## 维护建议

1. **不要轻易添加新脚本**
   - 如果可以组合现有脚本实现，就不要新建脚本
   - 保持bin目录简洁

2. **新建脚本必须遵循现有命名规范**
   - `prepare_xxx_to_json.py`：A格式转JSON
   - `prepare_xxx_sql.py`：JSON转SQL
   - `prepare_xxx_for_storage.py`：数据预处理

3. **定期审查**
   - 删除过时的脚本
   - 合并功能重复的脚本

---

**最后更新**: 2026-04-25
**脚本总数**: 12个（精简后）

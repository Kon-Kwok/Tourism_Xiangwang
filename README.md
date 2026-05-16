# 旅游自动化采集系统

> 基于Chrome登录态的电商数据自动化采集系统，支持飞猪、千牛、赤兔KPI等多数据源采集。

## 🎯 核心功能

### 1. 赤兔KPI客服数据（3个报表）

通过CDP自动化导出Excel报表，转换为JSON并入库。

- **人均日接入**（id=1721）→ `Xiangwang.customer_service_data_daily`
- **每周店铺个人数据**（id=1996）→ `Xiangwang.customer_service_performance_summary`
- **客服数据23年新**（id=2496）→ `Xiangwang.customer_service_performance_workload_analysis`

### 2. 飞猪订单列表

HTTP + Cookie采集订单数据，支持时间范围筛选、全页采集、订单明细入库，并将订单汇总指标写入千牛日度关键表。

→ `Xiangwang.order_list`
→ `Xiangwang.shop_daily_key_data`（`total_bookings`、`total_pax`、`gmv`）

### 3. SYCM流量看板

采集生意参谋流量监控数据（访客数、浏览量、广告/平台流量），写入同一张千牛日度关键表。

→ `Xiangwang.shop_daily_key_data`

## 🚀 快速开始

### 前置条件

```bash
# 1. 启动Chrome调试窗口
./bin/start-chrome-unified.sh

# 2. 登录相关网站
# 在Chrome中登录：sycm.taobao.com, fsc.fliggy.com, kf.topchitu.com
```

### 一键采集（推荐）

```bash
# 设置数据库连接
export HOST="your_mysql_host"
export PORT="your_mysql_port"
export USER="your_mysql_user"
export PASS="your_mysql_password"

# 一键采集所有业务
./skills/all.sh $(date -d "yesterday" +%Y-%m-%d)
```

详细操作步骤请查看 **[skills/README.md](./skills/README.md)** 或 **[AI业务操作指南.md](./AI业务操作指南.md)**

## 📁 项目结构

```
src/tourism_automation/
├── cli/                    # CLI命令入口
├── collectors/             # 数据采集器
│   ├── sycm/              # 生意参谋
│   ├── fliggy_home/       # 飞猪商家工作台
│   └── fliggy_kpi/        # 飞猪KPI（员工、店铺）
└── shared/                # 共享组件
bin/                       # 操作脚本
skills/                    # 一键执行脚本
result/                    # 结果和数据指南
docs/                      # 详细文档
```

## 📚 关键文档

- **[skills/README.md](./skills/README.md)** - 一键执行脚本使用指南
- **[skills/OPTIMIZATION.md](./skills/OPTIMIZATION.md)** - 性能优化迭代计划
- **[AI业务操作指南.md](./AI业务操作指南.md)** - 三个核心业务的完整操作流程
- **[result/README.md](./result/README.md)** - 业务操作快速指南
- **[CLAUDE.md](./CLAUDE.md)** - 项目开发指引

## 🔧 环境要求

- Python 3.10+
- MySQL 8.0+
- Chrome/Chromium（调试端口：9222）

## ⚠️ 重要提示

### Chrome会话管理
- 调试窗口必须一直运行，不要关闭
- 配置目录：`~/.config/google-chrome-debug`
- 启动脚本：`bin/start-chrome-unified.sh`

### 日期模式
- 赤兔KPI报表：**必须**使用 `--date-mode day`
- 使用 `--date-mode week` 会导出周报，导致SQL脚本报错

## 📊 数据库表结构

- **Xiangwang数据库**：客服KPI、订单数据、店铺数据、流量数据、SYCM数据

详见 `sql/` 目录中的建表SQL。

## 🛠️ 三个核心业务命令

```bash
# 业务1：赤兔KPI报表导出（必须用--date-mode day）
python3 -m tourism_automation.cli.main shop-kpi-export --report-name "人均日接入" --date-mode day --date YYYY-MM-DD

# 业务2：飞猪订单列表采集（必须 --all-pages，预处理后同时写订单明细和千牛订单汇总）
python3 -m tourism_automation.cli.main fliggy-order-list list --page-num 1 --page-size 100 --all-pages --deal-start "YYYY-MM-DD 00:00:00" --deal-end "YYYY-MM-DD 23:59:59"

# 业务3：SYCM流量看板采集
python3 -m tourism_automation.cli.main sycm flow-monitor --date YYYY-MM-DD --shop-name "皇家加勒比国际游轮旗舰店"
```

完整的数据转换和入库流程请查看 **[AI业务操作指南.md](./AI业务操作指南.md)**

## 📖 开发文档

- `CLAUDE.md` - 项目开发指引
- `docs/README.md` - 文档总入口
- `docs/architecture/` - 架构文档
- `docs/collectors/` - 采集器文档

---

**最后更新**: 2026-04-25

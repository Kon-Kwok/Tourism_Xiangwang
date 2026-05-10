---
name: daily-data-collection
description: 飞猪业务日报数据采集技能。一键采集四大核心日报数据（赤兔KPI客服报表、飞猪订单列表、SYCM流量看板、阿里妈妈投放日报）。当用户需要"日报数据"、"昨日数据采集"、"5月1日日报"或提及"KPI"、"订单"、"流量"、"阿里妈妈"、"直通车"、"万相台"等关键词时使用此技能。
---

# 每日数据采集技能

一键采集四大核心日报数据：赤兔KPI客服报表、飞猪订单列表、SYCM流量看板、阿里妈妈投放日报。

## 🚫 绝对禁止

1. **不要修改项目代码** — 源码在正确环境下能正常工作，出错一定是环境问题
2. **不要碰 Chrome** — 不要杀掉、重启、或自己启动 Chrome
3. **不要深入调试** — 不要研究 Cookie 加密、不要写调试脚本，第 2 次失败就报告用户

## 快速开始

### 一键采集所有数据

**重要**：所有命令都需要在项目根目录执行

```bash
cd ~/Tourism_Xiangwang
./scripts/all.sh [YYYY-MM-DD]
```

**示例**：
```bash
# 切换到项目目录
cd ~/Tourism_Xiangwang

# 采集昨天的数据
./scripts/all.sh

# 采集指定日期
./scripts/all.sh 2026-04-30

# 用户说“5月1日日报”时，解析为当年 2026-05-01
./scripts/all.sh 2026-05-01
```

### 单独采集某个模块

```bash
cd ~/Tourism_Xiangwang

# KPI报表
./scripts/kpi_reports.sh 2026-04-30

# 飞猪订单
./scripts/fliggy_orders.sh 2026-04-30

# SYCM流量
./scripts/sycm_flow.sh 2026-04-30

# 阿里妈妈投放日报（HTTP接口采集 + 入库）
./scripts/alimama_daily.sh 2026-05-01
```

## 环境配置

### 数据库配置

**创建 .env 文件**：
```bash
cd ~/Tourism_Xiangwang
cat > .env << EOF
HOST=your_mysql_host
PORT=3306
USER=your_mysql_user
PASS=your_mysql_password
EOF
```

**或设置环境变量**：
```bash
export HOST="your_mysql_host"
export PORT="3306"
export USER="your_mysql_user"
export PASS="your_mysql_password"
```

### 前置条件

采集前请确认：

1. **Chrome 在 WSL2 中运行**
   - 启动：`~/Tourism_Xiangwang/bin/start-chrome-unified.sh`
   - 检查：`ps aux | grep remote-debugging-port=9222`

2. **赤兔 KPI 页面已打开**
   - Chrome 中需有 `kf.topchitu.com/web/custom-kpi/employee-kpi?id=1721` 页面

3. **三个网站已登录**
   - sycm.taobao.com、fsc.fliggy.com、kf.topchitu.com

## 四大核心业务

| 业务 | 原理 | 耗时 | 目标表 |
|------|------|------|--------|
| 赤兔KPI客服报表 | CDP 操控 Chrome 导出 Excel → 入库 | ~30s | `fliggy_customer_service_*` |
| 飞猪订单列表 | Chrome cookie + HTTP API | ~5s | `fliggy_order_list` + `qianniu_*` |
| SYCM流量看板 | Chrome cookie + HTTP API | ~5s | `qianniu_fliggy_shop_daily_key_data` |
| 阿里妈妈投放日报 | Chrome cookie + HTTP API；必要时只用CDP发现一次性token | ~5s | `fliggy_star_store`、`fliggy_tmall_express`、`fliggy_gravity_rubiks_cube`、`fliggy_wanxiangtai`、`fliggy_wanxiangtai_2` |

## 阿里妈妈投放日报

触发方式：
- “我要 5月1日的日报” → 执行 `./scripts/all.sh 2026-05-01`
- “昨日日报” → 用系统昨日日期执行 `./scripts/all.sh YYYY-MM-DD`
- 只更新投放报表 → 执行 `./scripts/alimama_daily.sh YYYY-MM-DD`

HTTP 数据源：
- 明星店铺/品销宝：`https://brandsearch.taobao.com/report/query/rptAdvertiserSubListNew.json`
- 直通车、引力魔方、万相台/万相台2：`https://one.alimama.com/report/query.json`
- 直通车取 `关键词推广`，引力魔方取 `人群推广`。
- 万相台和万相台2是两张独立表；万相台2按 `数据源` 存 `超级短视频/超级直播/货品运营/全站推广/小计` 五行。

历史 Excel 参考：
- 项目根目录 `2026年阿里妈妈投放每日数据-更新到5.5(1).xlsx` 仅作为历史字段和公式口径参考。
- 日报执行不更新 Excel，只通过 HTTP 接口取数并写入 MySQL。
- 入库派生字段按历史 Excel 公式口径在代码中计算。

## 错误处理

```
"数据库连接参数未配置" → 设置环境变量或创建 .env 文件
"未找到店铺KPI页面"   → 在 Chrome 中打开 KPI 页面
卡在"导出 Excel"      → 检查 Chrome 是否正常运行
阿里妈妈提示未找到 one.alimama 页面 → 在统一 Chrome 中打开并登录万相台无界报表页
其他错误              → 把错误信息报告给用户
```

## 技术细节

### 公共函数库

所有脚本使用 `scripts/lib/common.sh` 公共函数库：

- **参数检查**：`check_date_argument`、`init_mysql`
- **统一输出**：`print_collection_start/end`、`print_step`、`print_success/error`
- **文件验证**：`check_file_not_empty`

### 重构优势

- **代码复用**：消除了37%的重复代码
- **一致性**：统一的错误处理和输出格式
- **可维护性**：修改公共逻辑只需更新 common.sh

## 文件结构

```
Xiangwang/
├── scripts/                        # 业务代码
│   ├── lib/common.sh              # 公共函数库
│   ├── all.sh                     # 一键采集
│   ├── kpi_reports.sh             # KPI报表
│   ├── fliggy_orders.sh           # 飞猪订单
│   └── sycm_flow.sh              # SYCM流量
├── .env.example                   # 配置模板

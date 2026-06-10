#!/bin/bash
# 店铺每日登记数据一键采集脚本
# 用途：采集并补齐 shop_data_daily_registration 所需数据
# 使用：./scripts/all.sh [YYYY-MM-DD]

set -e  # 遇到错误立即退出

# 引入公共函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# 参数检查
DATE="$(resolve_date_argument "$1")"

# 打印欢迎信息
echo -e "${GREEN}"
echo "========================================"
echo "   店铺每日登记数据采集"
echo "   日期：$DATE"
echo "========================================"
echo -e "${NC}"

# 记录开始时间
START_TIME=$(date +%s)

# 数据源1: 赤兔KPI三个报表（已停用：客户未订购赤兔平台，咨询人数改从 SYCM 服务页面采集）
# echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源1：赤兔KPI三个报表${NC}"
# "$SCRIPT_DIR/kpi_reports.sh" "$DATE"
# echo ""

# 数据源1: SYCM服务核心监控，用于补齐 店铺每日登记.咨询人数
echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源1：SYCM服务核心监控（咨询人数）${NC}"
"$SCRIPT_DIR/sycm_service.sh" "$DATE"
echo ""

# 数据源2: 飞猪订单列表，用于补齐 店铺每日登记.下单买家数 / 订单明细
echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源2：飞猪订单列表${NC}"
"$SCRIPT_DIR/fliggy_orders.sh" "$DATE"
echo ""

# 数据源2b: 新GMV（链路1 日历房 + 链路2 度假订单导出），覆盖 shop_daily_key_data.gmv
echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源2b：新GMV采集（日历房+度假订单）${NC}"
"$SCRIPT_DIR/gmv_combined.sh" "$DATE"
echo ""

# 数据源3: SYCM流量看板，直接写入 店铺每日登记.关注店铺人数，并提供 PV/UV/PaidUV 来源
echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源3：SYCM流量看板${NC}"
"$SCRIPT_DIR/sycm_flow.sh" "$DATE"
echo ""

# 阿里妈妈投放日报当前不参与“店铺每日登记”采集，先保留为注释。
# echo -e "${BLUE}[$(date +%H:%M:%S)] 数据源4：阿里妈妈投放日报${NC}"
# "$SCRIPT_DIR/alimama_daily.sh" "$DATE"
# echo ""

# 汇总: 只应用 店铺每日登记 所需跨表规则
echo -e "${BLUE}[$(date +%H:%M:%S)] 汇总：店铺每日登记跨表规则应用${NC}"
"$SCRIPT_DIR/apply_cross_table_rules.sh" "$DATE"
echo ""

# 计算耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# 打印完成信息
echo -e "${GREEN}"
echo "========================================"
echo "   ✓ 店铺每日登记数据采集完成！"
echo "   总耗时：${MINUTES}分${SECONDS}秒"
echo "========================================"
echo -e "${NC}"

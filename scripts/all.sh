#!/bin/bash
# 四大核心业务一键采集脚本
# 用途：一次性采集所有四个业务的数据
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
echo "   四大核心业务一键采集"
echo "   日期：$DATE"
echo "========================================"
echo -e "${NC}"

# 记录开始时间
START_TIME=$(date +%s)

# 业务1: 赤兔KPI三个报表
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务1：赤兔KPI三个报表${NC}"
"$SCRIPT_DIR/kpi_reports.sh" "$DATE"
echo ""

# 业务2: 飞猪订单列表
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务2：飞猪订单列表${NC}"
"$SCRIPT_DIR/fliggy_orders.sh" "$DATE"
echo ""

# 业务3: SYCM流量看板
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务3：SYCM流量看板${NC}"
"$SCRIPT_DIR/sycm_flow.sh" "$DATE"
echo ""

# 业务4: 阿里妈妈投放日报
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务4：阿里妈妈投放日报${NC}"
"$SCRIPT_DIR/alimama_daily.sh" "$DATE"
echo ""

# 业务5: 跨表规则应用
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务5：跨表规则应用${NC}"
"$SCRIPT_DIR/apply_cross_table_rules.sh" "$DATE"
echo ""

# 业务6: 赤兔团队看板采集
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务6：赤兔团队看板采集${NC}"
"$SCRIPT_DIR/team_dashboard.sh" "$DATE"
echo ""

# 业务7: 二次预约订单采集
echo -e "${BLUE}[$(date +%H:%M:%S)] 业务7：二次预约订单采集${NC}"
MONTH_START="${DATE}-01"
MONTH_END=$(python3 -c "from calendar import monthrange; d='${DATE}'.split('-'); print(f'{d[0]}-{d[1]}-{monthrange(int(d[0]),int(d[1]))[1]:02d}')" 2>/dev/null || echo "${DATE}-28")

if ! python3 -m tourism_automation.cli.main fliggy-secondary-order collect \
  --start-date "${MONTH_START}" \
  --end-date "${MONTH_END}"; then
    echo -e "${RED}=========================================${NC}"
    echo -e "${RED}✗ 二次预约订单采集失败，已停止日报生成${NC}"
    echo -e "${RED}  原因：避免 Excel 使用旧数据${NC}"
    echo -e "${RED}  请检查 Chrome 调试窗口和飞猪登录态${NC}"
    echo -e "${RED}=========================================${NC}"
    exit 1
fi
echo ""

# 计算耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# 打印完成信息
echo -e "${GREEN}"
echo "========================================"
echo "   ✓ 所有业务采集完成！"
echo "   总耗时：${MINUTES}分${SECONDS}秒"
echo "========================================"
echo -e "${NC}"

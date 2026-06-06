#!/bin/bash
# 赤兔KPI三个报表采集脚本
# 用途：采集、转换、入库赤兔KPI三个报表数据
# 使用：./scripts/kpi_reports.sh [YYYY-MM-DD]

set -eo pipefail  # 遇到错误立即退出，管道中任一命令失败即失败

# 引入公共函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# 参数检查
DATE="$(resolve_date_argument "$1")"

# 初始化数据库连接
MYSQL="$(init_mysql)"

# 打印开始标题
print_collection_start "赤兔KPI三个报表采集" "$DATE"

echo -e "${BLUE}[$(date +%H:%M:%S)] 跳转赤兔到自定义报表：人均日接入${NC}"
python3 bin/ensure_topchitu_custom_report.py \
  --watch-seconds "${TOPCHITU_CUSTOM_REPORT_WATCH_SECONDS:-30}" \
  >/tmp/topchitu_custom_report.log 2>&1 || true

# 报表列表
reports=(
  "人均日接入:prepare_customer_service_data_daily_sql.py"
  "每周店铺个人数据:prepare_customer_service_performance_summary_sql.py"
  "客服数据23年新:prepare_customer_service_performance_workload_sql.py"
)

# 处理每个报表
for item in "${reports[@]}"; do
  IFS=':' read -r report_name script_name <<< "$item"

  echo ""
  echo -e "${YELLOW}▶ 开始处理：$report_name${NC}"

  echo -e "  [1/2] 从赤兔网页接口读取..."
  echo -e "  [2/2] 转换并入库..."
  python3 bin/prepare_shop_kpi_api_to_json.py \
    --report-name "$report_name" \
    --date "$DATE" | \
    python3 "bin/$script_name" | \
    $MYSQL Xiangwang

  print_success "$report_name 处理完成"
done

# 打印完成标题
print_collection_end "所有报表处理"

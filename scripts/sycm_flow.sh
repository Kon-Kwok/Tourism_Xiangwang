#!/bin/bash
# SYCM流量看板采集脚本
# 用途：采集、转换、入库SYCM流量数据
# 使用：./scripts/sycm_flow.sh [YYYY-MM-DD]

set -e  # 遇到错误立即退出

# 引入公共函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# 参数检查
DATE="$(resolve_date_argument "$1")"

# 店铺名称（可由环境变量覆盖）
SHOP_NAME="${SHOP_NAME:-皇家加勒比国际游轮旗舰店}"

# 初始化数据库连接
MYSQL="$(init_mysql)"

# 打印开始标题
print_collection_start "SYCM流量看板采集" "$DATE" "店铺：$SHOP_NAME"

# 步骤1: 采集流量数据
print_step 1 3 "采集流量数据"
python3 -m tourism_automation.cli.main sycm flow-monitor \
  --date "$DATE" \
  --shop-name "$SHOP_NAME" > /tmp/sycm_flow_$$.json

if ! check_file_not_empty "/tmp/sycm_flow_$$.json" "未采集到流量数据"; then
  exit 1
fi
print_success "采集完成"

# 步骤2: 数据转换
print_step 2 3 "数据转换为SQL（含关注店铺人数）"
cat /tmp/sycm_flow_$$.json | \
  python3 bin/prepare_sycm_flow_sql.py > /tmp/sycm_flow_$$.sql

if ! check_file_not_empty "/tmp/sycm_flow_$$.sql" "SQL转换失败"; then
  rm -f /tmp/sycm_flow_$$.json
  exit 1
fi

if ! grep -q "shop_data_daily_registration" /tmp/sycm_flow_$$.sql; then
  print_error "SQL缺少关注店铺人数入库语句"
  rm -f /tmp/sycm_flow_$$.json /tmp/sycm_flow_$$.sql
  exit 1
fi
print_success "转换完成"

# 步骤3: 入库
print_step 3 3 "数据入库"
cat /tmp/sycm_flow_$$.sql | $MYSQL Xiangwang
print_success "入库完成"

# 清理临时文件
rm -f /tmp/sycm_flow_$$.json /tmp/sycm_flow_$$.sql

# 打印完成标题
print_collection_end "SYCM流量采集"

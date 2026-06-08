#!/bin/bash
# SYCM 服务核心监控采集脚本
# 用途：从 SYCM 服务页面采集咨询人数，写入店铺每日登记
# 使用：./scripts/sycm_service.sh [YYYY-MM-DD]

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

DATE="$(resolve_date_argument "$1")"
MYSQL="$(init_mysql)"

print_collection_start "SYCM服务核心监控采集" "$DATE"

# 步骤1: 采集咨询人数
print_step 1 3 "采集咨询人数（SYCM服务核心监控）"
python3 bin/prepare_sycm_service_to_json.py --date "$DATE" > /tmp/sycm_service_$$.json

if ! check_file_not_empty "/tmp/sycm_service_$$.json" "未采集到SYCM服务数据"; then
  exit 1
fi

CONSULT_COUNT=$(jq '.rows[0]["咨询人数"]' /tmp/sycm_service_$$.json 2>/dev/null || echo "0")
print_success "咨询人数: $CONSULT_COUNT"

# 步骤2: 数据转换为SQL
print_step 2 3 "数据转换为SQL"
cat /tmp/sycm_service_$$.json | \
  python3 bin/prepare_sycm_service_sql.py > /tmp/sycm_service_$$.sql

if ! check_file_not_empty "/tmp/sycm_service_$$.sql" "SQL转换失败"; then
  rm -f /tmp/sycm_service_$$.json
  exit 1
fi
print_success "转换完成"

# 步骤3: 入库
print_step 3 3 "数据入库"
cat /tmp/sycm_service_$$.sql | $MYSQL Xiangwang
print_success "入库完成"

# 清理临时文件
rm -f /tmp/sycm_service_$$.json /tmp/sycm_service_$$.sql

print_collection_end "SYCM服务核心监控采集" "咨询人数：$CONSULT_COUNT"

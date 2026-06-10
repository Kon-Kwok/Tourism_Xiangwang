#!/bin/bash
# 新 GMV 采集脚本
# 用途：链路1(日历房) + 链路2(度假订单) = 新 GMV，写入 shop_daily_key_data.gmv
# 使用：./scripts/gmv_combined.sh [YYYY-MM-DD]

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

DATE="$(resolve_date_argument "$1")"
MYSQL="$(init_mysql)"

print_collection_start "新GMV采集（日历房+度假订单）" "$DATE"

# 步骤1: 采集两条链路
print_step 1 3 "采集链路1(日历房) + 链路2(度假订单导出)..."
python3 bin/prepare_gmv_combined_to_json.py --date "$DATE" > /tmp/gmv_combined_$$.json

if ! check_file_not_empty "/tmp/gmv_combined_$$.json" "GMV采集失败"; then
  exit 1
fi

GMV_TOTAL=$(jq '.summary.gmv_total' /tmp/gmv_combined_$$.json 2>/dev/null || echo "0")
print_success "GMV合计: $GMV_TOTAL"

# 步骤2: 数据转换为SQL
print_step 2 3 "数据转换为SQL"
cat /tmp/gmv_combined_$$.json | \
  python3 bin/prepare_gmv_combined_sql.py > /tmp/gmv_combined_$$.sql

if ! check_file_not_empty "/tmp/gmv_combined_$$.sql" "SQL转换失败"; then
  rm -f /tmp/gmv_combined_$$.json
  exit 1
fi
print_success "转换完成"

# 步骤3: 入库
print_step 3 3 "数据入库"
cat /tmp/gmv_combined_$$.sql | $MYSQL Xiangwang
print_success "入库完成"

# 清理临时文件
rm -f /tmp/gmv_combined_$$.json /tmp/gmv_combined_$$.sql

print_collection_end "新GMV采集" "GMV合计: $GMV_TOTAL"

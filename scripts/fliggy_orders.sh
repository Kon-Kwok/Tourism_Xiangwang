#!/bin/bash
# 飞猪订单列表采集脚本
# 用途：采集、转换、入库飞猪订单数据
# 使用：./scripts/fliggy_orders.sh [YYYY-MM-DD]

set -eo pipefail  # 遇到错误立即退出

# 引入公共函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# 参数检查
DATE="$(resolve_date_argument "$1")"

# 数据库连接
MYSQL="$(init_mysql)"

# 打印开始标题
print_collection_start "飞猪订单列表采集" "$DATE"

MAX_RETRIES=3
RETRY_DELAY=5

# 步骤1: 采集订单数据（带重试）
print_step 1 4 "采集订单数据"
ORDER_COUNT=0
for attempt in $(seq 1 $MAX_RETRIES); do
  python3 -m tourism_automation.cli.main fliggy-order-list list \
    --page-num 1 \
    --page-size 20 \
    --all-pages \
    --deal-start "${DATE} 00:00:00" \
    --deal-end "${DATE} 23:59:59" > /tmp/orders_raw_$$.json

  if ! check_file_not_empty "/tmp/orders_raw_$$.json" "未采集到订单数据"; then
    exit 1
  fi

  ORDER_COUNT=$(jq '.rows | length' /tmp/orders_raw_$$.json 2>/dev/null || echo "0")
  TOTAL_PAGE=$(jq '.summary.total_page' /tmp/orders_raw_$$.json 2>/dev/null || echo "0")

  if [ "$ORDER_COUNT" -gt 0 ]; then
    break
  fi

  if [ "$attempt" -lt "$MAX_RETRIES" ]; then
    echo -e "  ${YELLOW}⚠ 订单数为0（totalPage=$TOTAL_PAGE），${RETRY_DELAY}秒后重试 ($attempt/$MAX_RETRIES)${NC}"
    sleep $RETRY_DELAY
  fi
done

print_success "采集到 $ORDER_COUNT 条订单"

# 步骤2: 数据预处理
print_step 2 4 "数据预处理"
cat /tmp/orders_raw_$$.json | \
  python3 bin/prepare_order_list_for_storage.py > /tmp/orders_prep_$$.json
print_success "预处理完成"

# 步骤3: 订单明细入库
print_step 3 4 "订单明细入库"
cat /tmp/orders_prep_$$.json | \
  python3 bin/prepare_order_list_sql.py | \
  $MYSQL Xiangwang
print_success "订单明细入库完成"

# 步骤4: 订单汇总入库
print_step 4 4 "订单汇总入库"
cat /tmp/orders_prep_$$.json | \
  python3 bin/prepare_shop_daily_key_sql.py | \
  $MYSQL Xiangwang
print_success "订单汇总入库完成"

# 清理临时文件
rm -f /tmp/orders_raw_$$.json /tmp/orders_prep_$$.json

# 打印完成标题
print_collection_end "飞猪订单采集" "订单数量：$ORDER_COUNT"

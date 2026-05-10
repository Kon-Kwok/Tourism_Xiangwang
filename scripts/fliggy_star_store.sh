#!/bin/bash
# 飞猪明星店铺报表采集
# 使用：./scripts/star_store.sh YYYY-MM-DD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

check_date_argument "$1"
DATE=$1

echo "========================================"
echo "飞猪明星店铺报表采集"
echo "日期：$DATE"
echo "========================================"

DB_HOST="${HOST:-127.0.0.1}"
DB_PORT="${PORT:-3306}"
DB_USER="${MYSQL_USER:-${DB_USER:-remote_user}}"
DB_PASS="${PASS:-}"

python3 -m tourism_automation.cli.main fliggy-star-store collect \
  --date "$DATE" \
  --save \
  --mysql-host "$DB_HOST" \
  --mysql-port "$DB_PORT" \
  --mysql-user "$DB_USER" \
  --mysql-password "$DB_PASS" \
  --mysql-database Xiangwang \
  --omit-raw

echo "✓ 飞猪明星店铺报表采集完成"

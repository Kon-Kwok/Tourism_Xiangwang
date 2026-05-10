#!/bin/bash
# 阿里妈妈投放日报采集脚本
# 使用：./scripts/alimama_daily.sh YYYY-MM-DD

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

check_date_argument "$1"
DATE=$1

print_collection_start "阿里妈妈投放日报采集" "$DATE"

DB_HOST="${HOST:-127.0.0.1}"
DB_PORT="${PORT:-3306}"
DB_USER="${MYSQL_USER:-${DB_USER:-${USER:-remote_user}}}"
DB_PASS="${PASS:-}"

python3 -m tourism_automation.cli.main alimama-daily collect \
  --date "$DATE" \
  --save \
  --mysql-host "$DB_HOST" \
  --mysql-port "$DB_PORT" \
  --mysql-user "$DB_USER" \
  --mysql-password "$DB_PASS" \
  --mysql-database Xiangwang \
  --omit-raw

print_collection_end "阿里妈妈投放日报采集"

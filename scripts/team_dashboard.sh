#!/bin/bash
# 赤兔团队看板数据采集脚本
# 用途：从赤兔团队看板采集首次响应时间和平均响应时间
# 使用：./scripts/team_dashboard.sh [YYYY-MM-DD]

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

DATE="$(resolve_date_argument "$1")"

print_collection_start "赤兔团队看板采集" "$DATE"

python3 "${PROJECT_ROOT}/bin/prepare_team_dashboard.py" --date "$DATE"

print_collection_end "赤兔团队看板采集"

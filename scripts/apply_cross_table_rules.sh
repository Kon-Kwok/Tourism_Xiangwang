#!/bin/bash
# 跨表规则应用脚本 —— 采集完成后补齐 shop_daily_key_data / shop_data_daily_registration 衍生字段
# 使用：./scripts/apply_cross_table_rules.sh [YYYY-MM-DD]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

DATE="$(resolve_date_argument "$1")"
MYSQL_CMD="$(init_mysql)"

print_collection_start "跨表规则应用" "$DATE"

# ============================================================
MYSQL_EXEC="${MYSQL_CMD} xiangwang --skip-column-names"

echo ""
echo -e "${YELLOW}▶ [1/8] 阿里妈妈投放数据写入店铺日度关键数据${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_daily_key_data sd,
       (SELECT CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL(14,2)) AS c, imp AS i, click AS cl FROM star_store WHERE date_time='${DATE}') src
SET sd.pingxiaobao_cost=src.c, sd.pingxiaobao_imp=src.i, sd.pingxiaobao_click=src.cl WHERE sd.日期='${DATE}';

UPDATE shop_daily_key_data sd,
       (SELECT CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL(14,2)) AS c, imp AS i, click AS cl FROM tmall_express WHERE date_time='${DATE}') src
SET sd.tmall_express_cost=src.c, sd.tmall_express_imp=src.i, sd.tmall_express_click=src.cl WHERE sd.日期='${DATE}';

UPDATE shop_daily_key_data sd,
       (SELECT CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL(14,2)) AS c, imp AS i, click AS cl FROM gravity_rubiks_cube WHERE date_time='${DATE}') src
SET sd.gravity_rubiks_cube_cost=src.c, sd.gravity_rubiks_cube_imp=src.i, sd.gravity_rubiks_cube_click=src.cl WHERE sd.日期='${DATE}';

UPDATE shop_daily_key_data sd,
       (SELECT CAST(REPLACE(REPLACE(cost,'￥',''),',','') AS DECIMAL(14,2)) AS c, imp AS i, click AS cl FROM wanxiangtai WHERE date_time='${DATE}') src
SET sd.mansa_dae_cost=src.c, sd.mansa_dae_views=src.i, sd.mansa_dae_click=src.cl WHERE sd.日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 阿里妈妈投放数据写入完成${NC}"

echo -e "${YELLOW}▶ [2/8] KPI询单人数汇总 → chat_volume${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_daily_key_data sd,
       (SELECT SUM(IF(询单人数 REGEXP '^[0-9]+$', 询单人数, 0)) AS total FROM customer_service_performance_summary WHERE date_time='${DATE}') src
SET sd.chat_volume = src.total WHERE sd.日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ chat_volume 写入完成${NC}"

echo -e "${YELLOW}▶ [3/8] 四个渠道 booked_cabin 默认值 = 3${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_daily_key_data
SET pingxiaobao_booked_cabin=3, tmall_express_booked_cabin=3,
    gravity_rubiks_cube_booked_cabin=3, mansa_dae_booked_cabin=3
WHERE 日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ booked_cabin 写入完成${NC}"

echo -e "${YELLOW}▶ [4/8] 流量来源汇总 & 直引万品点击量${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_daily_key_data
SET 流量来源汇总 = 流量来源广告_uv + 流量来源平台_uv,
    直引万品点击量 = COALESCE(pingxiaobao_click,0) + COALESCE(tmall_express_click,0)
                  + COALESCE(gravity_rubiks_cube_click,0) + COALESCE(mansa_dae_click,0)
WHERE 日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 流量来源汇总 & 直引万品点击量 计算完成${NC}"

echo -e "${YELLOW}▶ [5/8] 投放汇总 cost_total / imp_total / click_total${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_daily_key_data
SET cost_total  = COALESCE(pingxiaobao_cost,0) + COALESCE(tmall_express_cost,0)
                + COALESCE(gravity_rubiks_cube_cost,0) + COALESCE(mansa_dae_cost,0),
    imp_total   = COALESCE(pingxiaobao_imp,0) + COALESCE(tmall_express_imp,0)
                + COALESCE(gravity_rubiks_cube_imp,0) + COALESCE(mansa_dae_views,0),
    click_total = COALESCE(pingxiaobao_click,0) + COALESCE(tmall_express_click,0)
                + COALESCE(gravity_rubiks_cube_click,0) + COALESCE(mansa_dae_click,0)
WHERE 日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 投放汇总字段计算完成${NC}"

echo -e "${YELLOW}▶ [6/8] shop_daily_key_data → shop_data_daily_registration${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_data_daily_registration dr,
       (SELECT total_pv, total_uv, gmv, 直引万品点击量, total_bookings
        FROM shop_daily_key_data WHERE 日期='${DATE}') src
SET dr.PV=src.total_pv, dr.UV=src.total_uv, dr.GMV=src.gmv,
    dr.PaidUV=src.直引万品点击量, dr.下单买家数=src.total_bookings
WHERE dr.日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 5 个字段复制完成${NC}"

echo -e "${YELLOW}▶ [7/8] KPI咨询人数汇总 → 店铺每日登记.咨询人数${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_data_daily_registration dr,
       (SELECT SUM(咨询人数) AS total FROM customer_service_performance_summary WHERE date_time='${DATE}') src
SET dr.咨询人数 = src.total WHERE dr.日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 咨询人数写入完成${NC}"

echo -e "${YELLOW}▶ [8/8] 咨询转化率 & 下单转化率${NC}"
${MYSQL_EXEC} 2>/dev/null <<SQL
UPDATE shop_data_daily_registration
SET 咨询转化率 = CASE WHEN 咨询人数 > 0 THEN 下单买家数 / 咨询人数 ELSE NULL END,
    下单转化率 = CASE WHEN UV > 0 THEN 下单买家数 / UV ELSE NULL END
WHERE 日期='${DATE}';
SQL
echo -e "  ${GREEN}✓ 转化率计算完成${NC}"

print_collection_end "跨表规则应用"

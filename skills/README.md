# Skills - 快速执行脚本

四大核心业务的快速执行脚本。

## 📋 脚本列表

| 脚本 | 业务 | 用途 |
|------|------|------|
| `kpi_reports.sh` | 赤兔KPI三个报表 | 采集、转换、入库客服数据 |
| `fliggy_orders.sh` | 飞猪订单列表 | 采集、转换、入库订单明细，并同步 `gmv`、`total_bookings`、`total_pax` 到店铺日度关键表 |
| `sycm_flow.sh` | SYCM流量看板 | 采集、转换、入库流量数据和关注店铺人数 |
| `alimama_daily.sh` | 阿里妈妈投放日报 | 采集、计算、入库明星店铺/直通车/引力魔方/万相台/万相台2 |
| `all.sh` | 全部业务 | 一键执行所有四个业务 |

## 🚀 使用方法

### 1. 配置数据库连接（首次使用）

```bash
# 推荐：项目根目录 .env 会被 scripts/lib/common.sh 自动加载
cat > .env << EOF
HOST=localhost
PORT=3306
USER=remote_user
PASS=your_mysql_password
EOF

# 或者一次性设置
export MYSQL_CMD="mysql -h $HOST -P $PORT -u $USER -p$PASS"
```

### 2. 给脚本添加执行权限

```bash
chmod +x scripts/*.sh
```

### 3. 执行单个业务

```bash
# 赤兔KPI三个报表
./scripts/kpi_reports.sh 2026-04-24

# 飞猪订单列表
./scripts/fliggy_orders.sh 2026-04-24

# SYCM流量看板
./scripts/sycm_flow.sh 2026-04-24

# 阿里妈妈投放日报
./scripts/alimama_daily.sh 2026-04-24
```

### 4. 一键执行所有业务

```bash
# 采集昨日数据
./scripts/all.sh

# 采集指定日期
./scripts/all.sh 2026-04-24
```

## ⚡ 性能优化建议

### 当前版本（v1）

- ✅ 串行执行各个报表
- ✅ 下载完成后立即继续，超时由 `KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS` 控制
- ✅ 基本错误处理

### 下一步优化方向

- [ ] 并行导出多个报表（减少总等待时间）
- [x] 智能等待机制（检测文件是否下载完成）
- [ ] 失败重试机制
- [ ] 进度条显示
- [ ] 详细的性能统计

## 🔍 验证数据

执行完成后，可以验证数据是否成功入库：

```bash
# 验证赤兔KPI数据
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang << EOF
SELECT '报表1' as 类型, COUNT(*) FROM customer_service_data_daily WHERE 日期 = '2026-04-24'
UNION ALL
SELECT '报表2', COUNT(*) FROM customer_service_performance_summary WHERE date_time = '2026-04-24'
UNION ALL
SELECT '报表3', COUNT(*) FROM customer_service_performance_workload_analysis WHERE date_time = '2026-04-24';
EOF

# 验证飞猪订单数据
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang \
  -e "SELECT COUNT(*) as 订单数 FROM order_list WHERE order_date = '2026-04-24';"

# 验证飞猪订单汇总数据
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang \
  -e "SELECT 日期, total_bookings, total_pax, gmv FROM shop_daily_key_data WHERE 日期 = '2026-04-24';"

# 验证SYCM流量数据
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang \
  -e "SELECT 日期, total_uv as 访客数, total_pv as 浏览量 FROM shop_daily_key_data WHERE 日期 = '2026-04-24';"

# 验证关注店铺人数
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang \
  -e "SELECT 日期, 关注店铺人数 FROM shop_data_daily_registration WHERE 日期 = '2026-04-24';"

# 验证阿里妈妈投放日报
mysql -h $HOST -P $PORT -u $USER -p$PASS Xiangwang \
  -e "SELECT COUNT(*) as 万相台2行数 FROM wanxiangtai_2 WHERE date_time = '2026-04-24';"
```

## 📊 性能记录

| 版本 | 优化措施 | 预计耗时 |
|------|----------|----------|
| v1 | 基础版本 | ~5分钟 |
| v2 | 并行导出 | ~3分钟 |
| v3 | 智能等待 | ~2分钟 |

## 🛠️ 故障排查

### 问题1：未找到Excel文件

**原因**：下载还未完成或日期模式错误

**解决**：
- 检查是否使用了 `--date-mode day`
- 设置 `KPI_DOWNLOAD_WAIT_TIMEOUT_SECONDS` 增加下载完成检测的超时时间
- 手动检查下载目录：`ls -lt ~/Downloads/*.xlsx`

### 问题2：MySQL连接失败

**原因**：环境变量未设置或连接信息错误

**解决**：
```bash
# 检查环境变量
echo $HOST $PORT $USER $PASS

# 测试连接
mysql -h $HOST -P $PORT -u $USER -p$PASS
```

### 问题3：采集到空数据

**原因**：Chrome会话过期或未登录

**解决**：
1. 检查Chrome调试窗口是否运行：`ps aux | grep "remote-debugging-port=9222"`
2. 在Chrome中重新登录相关网站
3. 重启Chrome调试窗口：`./bin/start-chrome-unified.sh`

---

**最后更新**: 2026-04-25
**当前版本**: v1

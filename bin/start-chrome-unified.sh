#!/bin/bash
# 启动统一的调试Chrome

set -e

DEBUG_PORT=9222
CONFIG_DIR="$HOME/.config/google-chrome-debug"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFRESH_SCRIPT="$SCRIPT_DIR/refresh_chrome_tabs.py"
REFRESH_INTERVAL="${CHROME_REFRESH_INTERVAL_SECONDS:-1800}"
REFRESH_INITIAL_DELAY="${CHROME_REFRESH_INITIAL_DELAY_SECONDS:-1800}"
REFRESH_LOG="${CHROME_REFRESH_LOG:-/tmp/chrome_refresh.log}"
REFRESH_PID_FILE="${CHROME_REFRESH_PID_FILE:-/tmp/chrome_refresh_${DEBUG_PORT}.pid}"
REFRESH_DOMAINS="${CHROME_REFRESH_DOMAINS:-sycm.taobao.com,fsc.fliggy.com,kf.topchitu.com,brandsearch.taobao.com,branding.taobao.com,one.alimama.com}"

stop_refresh_daemon() {
    local refresh_pid=""
    if [ -f "$REFRESH_PID_FILE" ] && read -r refresh_pid < "$REFRESH_PID_FILE"; then
        if [ -n "$refresh_pid" ] && kill -0 "$refresh_pid" > /dev/null 2>&1; then
            echo "正在关闭旧刷新守护进程..."
            kill "$refresh_pid" > /dev/null 2>&1 || true
            sleep 1
        fi
    fi
    rm -f "$REFRESH_PID_FILE"
}

start_refresh_daemon() {
    if [ "${CHROME_REFRESH_ENABLED:-1}" = "0" ]; then
        echo "自动刷新已禁用"
        return
    fi

    if [ ! -x "$REFRESH_SCRIPT" ]; then
        echo "未找到自动刷新脚本: $REFRESH_SCRIPT"
        return
    fi

    local refresh_pid=""
    if [ -f "$REFRESH_PID_FILE" ] && read -r refresh_pid < "$REFRESH_PID_FILE"; then
        if [ -n "$refresh_pid" ] && kill -0 "$refresh_pid" > /dev/null 2>&1; then
            echo "✓ 自动刷新守护进程已运行 PID: $refresh_pid"
            return
        fi
        rm -f "$REFRESH_PID_FILE"
    fi

    nohup python3 "$REFRESH_SCRIPT" \
      --port "$DEBUG_PORT" \
      --interval "$REFRESH_INTERVAL" \
      --initial-delay "$REFRESH_INITIAL_DELAY" \
      --domains "$REFRESH_DOMAINS" \
      --pid-file "$REFRESH_PID_FILE" \
      >> "$REFRESH_LOG" 2>&1 &

    refresh_pid=$!
    sleep 1
    if kill -0 "$refresh_pid" > /dev/null 2>&1; then
        echo "✓ 自动刷新守护进程 PID: $refresh_pid"
        echo "  刷新间隔: ${REFRESH_INTERVAL} 秒"
        echo "  首次刷新延迟: ${REFRESH_INITIAL_DELAY} 秒"
        echo "  刷新日志: $REFRESH_LOG"
    else
        echo "⚠ 自动刷新守护进程启动失败，查看日志: $REFRESH_LOG"
    fi
}

# 常用登录页。可以用 CHROME_START_URLS 覆盖，多个 URL 用空格分隔。
if [ -n "${CHROME_START_URLS:-}" ]; then
    read -r -a START_URLS <<< "$CHROME_START_URLS"
else
    START_URLS=(
        "https://sycm.taobao.com/portal/home.htm"
        "https://fsc.fliggy.com/#/new/home"
        "https://kf.topchitu.com/web/custom-kpi/employee-kpi?id=1721&wwt=ALL"
        "https://one.alimama.com/index.html"
        "https://branding.taobao.com/index.action"
    )
fi

echo "======================================"
echo "启动统一Chrome"
echo "======================================"
echo ""

# 1. 关闭旧的调试Chrome
echo "步骤 1/4: 清理..."
stop_refresh_daemon
if pgrep -f "chrome.*--remote-debugging-port=$DEBUG_PORT" > /dev/null 2>&1; then
    echo "正在关闭旧Chrome..."
    pkill -9 -f "chrome.*--remote-debugging-port=$DEBUG_PORT" || true
    sleep 2
fi
echo "✓ 清理完成"
echo ""

# 2. 创建配置目录
echo "步骤 2/4: 准备配置..."
mkdir -p "$CONFIG_DIR"
echo "✓ 配置目录: $CONFIG_DIR"
echo ""

# 3. 启动Chrome
echo "步骤 3/4: 启动Chrome..."
LIBGL_ALWAYS_SOFTWARE=1 nohup google-chrome \
  --remote-debugging-port=$DEBUG_PORT \
  --user-data-dir="$CONFIG_DIR" \
  --no-first-run \
  --no-default-browser-check \
  "${START_URLS[@]}" \
  > /tmp/chrome_debug.log 2>&1 &

CHROME_PID=$!
echo "✓ Chrome PID: $CHROME_PID"
echo ""

# 4. 等待并验证
echo "步骤 4/4: 验证..."
sleep 6

# 等待Chrome启动并创建配置
for i in {1..15}; do
    if curl -s http://localhost:$DEBUG_PORT/json/version > /dev/null 2>&1; then
# 创建DevToolsActivePort文件
        mkdir -p "$CONFIG_DIR/Default"
        # 获取浏览器WebSocket URL
        BROWSER_WS=$(curl -s http://localhost:$DEBUG_PORT/json/version | jq -r '.webSocketDebuggerUrl' | sed 's|ws://[^:]*:[0-9]*/||')
        echo -e "${DEBUG_PORT}\n${BROWSER_WS}" > "$CONFIG_DIR/Default/DevToolsActivePort"

        echo "✓ Chrome调试端口已就绪！"
        start_refresh_daemon
        echo ""
        echo "======================================"
        echo "✓ 启动成功！"
        echo "======================================"
        echo ""
        echo "这是你的统一Chrome浏览器："
        echo "  - 所有登录都在这个Chrome中"
        echo "  - 支持CDP数据采集"
        echo "  - 登录状态永久保存"
        echo "  - 已打开常用登录页：SYCM、飞猪、赤兔、阿里妈妈、万相台/直通车/引力魔方/品销宝入口"
        echo "  - 已启用业务标签页自动刷新，默认每30分钟刷新一次"
        echo ""
        echo "现在可以："
        echo "  1. 登录所有需要的网站"
        echo "  2. 采集KPI数据"
        echo ""
        echo "采集数据命令："
        echo "  python3 -m tourism_automation.cli.main fliggy-kpi employee --date 2026-04-19 --method api"
        echo ""
        echo "管理Chrome："
        echo "  查看日志: tail -f /tmp/chrome_debug.log"
        echo "  查看刷新日志: tail -f $REFRESH_LOG"
        echo "  停止Chrome: pkill -f 'chrome.*remote-debugging-port=$DEBUG_PORT'"
        echo "  停止自动刷新: kill \$(cat $REFRESH_PID_FILE)"
        echo "  重启Chrome: ./bin/start-chrome-unified.sh"
        echo ""
        exit 0
    fi
    echo "等待中... ($i/15)"
    sleep 2
done

echo "✗ Chrome启动失败"
echo ""
echo "请检查："
echo "  1. 查看日志: cat /tmp/chrome_debug.log"
echo "  2. 检查进程: ps aux | grep chrome"

pkill -9 -f "chrome.*--remote-debugging-port=$DEBUG_PORT" || true
exit 1

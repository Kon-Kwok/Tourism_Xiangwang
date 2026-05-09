---
name: refresh-chrome-tabs
description: 定时刷新 WSL Chrome 中三个业务标签页（飞猪、SYCM、赤兔），保持 Cookie 活跃。当用户说"刷新标签页"、"刷新Chrome"、"刷新页面"、"定时刷新"时触发。
---

# Chrome 标签页定时刷新

## 触发词
- "刷新标签页"
- "刷新Chrome"
- "刷新页面"
- "定时刷新"
- "查看刷新状态"

## 功能
通过 CDP 协议（Chrome DevTools Protocol）刷新三个业务标签页：
1. **飞猪商家工作台** — fsc.fliggy.com
2. **生意参谋** — sycm.taobao.com
3. **赤兔KPI** — kf.topchitu.com

## 执行方式

### 手动刷新
```bash
wsl bash /mnt/c/Users/Gzk/.openclaw/workspace/scripts/refresh_chrome_tabs.sh
```

### 定时任务（已配置）
```
*/30 8-21 * * * — 每天 8:00-21:30，每30分钟自动刷新
```

### 查看状态
```bash
# 查看定时任务
wsl bash -c "crontab -l"

# 查看刷新日志
wsl bash -c "cat /tmp/refresh_tabs.log | tail -20"

# 查看 Chrome 调试端口
wsl bash -c "curl -s http://localhost:9222/json | python3 -m json.tool | grep url"
```

## 前提条件
- Chrome 以 `--remote-debugging-port=9222` 启动
- 三个标签页已打开并登录
- Python3 + websockets 库已安装

## 文件位置
- 脚本：`/mnt/c/Users/Gzk/.openclaw/workspace/scripts/refresh_chrome_tabs.sh`
- 日志：`/tmp/refresh_tabs.log`

## 错误处理
- "Chrome 未运行" → 先启动 Chrome：`~/Tourism_Xiangwang/bin/start-chrome-unified.sh`
- "未找到标签页" → 确认三个页面已在 Chrome 中打开
- "刷新失败" → 检查 websockets 库：`pip3 install websockets --break-system-packages`

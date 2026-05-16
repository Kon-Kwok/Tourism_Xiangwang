# 项目结构标准化重构设计

## 目标

把当前分散在仓库根目录的 `sycm/` 与 `fliggy_home/` 采集器重构到统一的 `src/` 代码根下，抽出共享的 Chrome 登录态与 HTTP 能力，增加统一 CLI 入口，并保持现有采集行为不变。

本次重构不处理 `sql/` 目录规范，也不恢复入库功能。

## 目录结构

重构后的主结构：

```text
src/
  tourism_automation/
    cli/
      main.py
    collectors/
      sycm/
      fliggy_home/
    shared/
      chrome/
      http/
      result/
tests/
  cli/
  collectors/
docs/
  architecture/
  collectors/
```

## 模块边界

- `collectors/sycm/`：只负责生意参谋首页采集逻辑
- `collectors/fliggy_home/`：只负责飞猪商家工作台首页采集逻辑
- `shared/chrome/`：只负责读取本机 Chrome 登录态并构造已登录 session
- `shared/http/`：只负责通用 JSON 请求包装
- `shared/result/`：只负责模块化结果汇总
- `cli/main.py`：只负责统一命令分发

## 命令入口

统一命令形式：

```bash
python3 -m tourism_automation.cli.main sycm healthcheck
python3 -m tourism_automation.cli.main sycm collect-home --date 2026-04-19 --shop-name "皇家加勒比国际游轮旗舰店"
python3 -m tourism_automation.cli.main fliggy-home collect-home --date 2026-04-19 --shop-name "皇家加勒比国际游轮旗舰店"
```

## 运行方式

为避免必须先手工设置 `PYTHONPATH`，仓库根目录提供自动把 `src/` 加入模块搜索路径的运行时适配。

测试与本地命令都基于 `python3` 直接运行，不要求先安装包。

## 文档

新增：

- `docs/architecture/project-structure.md`
- `docs/collectors/sycm.md`
- `docs/collectors/fliggy-home.md`

文档只说明结构、命令和输出，不重复历史设计过程。

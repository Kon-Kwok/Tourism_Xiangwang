---
name: alimama-channel-import
description: 阿里妈妈推广渠道数据导入技能。当用户说"复制 x 日渠道数据"、"导入 x 日推广数据"、"写入 x 日渠道数据"时触发。从阿里妈妈 Excel 提取指定日期的4个渠道（明星店铺/品销宝、直通车、引力魔方、万象台）Cost/IMP/Click，写入 MySQL。
---

# 阿里妈妈推广渠道数据导入

## 触发词
- "复制 x 日渠道数据"
- "导入 x 日推广数据"
- "写入 x 日渠道数据"
- "把 x 日的渠道数据更新一下"

## 数据来源
Excel 文件：`C:\Users\Gzk\.openclaw\media\inbound\2026年阿里妈妈投放每日数据4.14revised---a68ba2ce-c674-460a-8458-3363561ee7eb.xlsx`

⚠️ 如果文件不存在，告诉用户把阿里妈妈 Excel 发过来。

## Excel Sheet 与 MySQL 字段映射

| Excel Sheet | MySQL 字段前缀 | 说明 |
|-------------|---------------|------|
| 明星店铺 | `pingxiaobao_` | 品销宝 |
| 直通车 | `tmall_express_` | 直通车 |
| 引力魔方 | `gravity_rubiks_cube_` | 引力魔方 |
| 万象台 | `mansa_dae_` | 万象台（注意：IMP 对应 `mansa_dae_views` 字段） |

每个渠道写入3个字段：`{前缀}cost`, `{前缀}imp`（万象台为 views）, `{前缀}click`

汇总字段：
- `cost_total` = 4个渠道 cost 之和
- `imp_total` = 4个渠道 imp 之和
- `click_total` = 4个渠道 click 之和

## 执行步骤

### 1. 用 Python 提取 Excel 数据

```python
import openpyxl
from datetime import datetime

wb = openpyxl.load_workbook(r'Excel文件路径', data_only=True)

target = 'YYYY-MM-DD'  # 用户指定的日期

# 4个 sheet（按 sheet 顺序，需要遍历匹配）
# Sheet 名称可能是乱码，通过特征识别：
# - 明星店铺：约1479行，20列
# - 直通车：约1479行，19列
# - 引力魔方：约1378行，17列
# - 万象台：约967行，16列

# 遍历所有 row>=100 的 sheet，找 Date 列中匹配 target 的行
# 取 row[1]=Cost, row[2]=IMP, row[3]=Click
```

按行数和列数识别渠道：
- 行数 ~1479, 列数 20 → 明星店铺
- 行数 ~1479, 列数 19 → 直通车
- 行数 ~1378, 列数 17 → 引力魔方
- 行数 ~967, 列数 16 → 万象台

### 2. 检查 MySQL 记录

```bash
wsl bash -c "mysql -hlocalhost -P3306 -uremote_user -pTourism2024 --default-character-set=utf8mb4 -e \"SELECT id, 日期 FROM qianniu.qianniu_fliggy_shop_daily_key_data WHERE 日期 = 'YYYY-MM-DD';\" 2>&1 | grep -v Warning"
```

- **有记录** → UPDATE
- **无记录** → INSERT（仅写入推广字段，其他字段留 NULL）

### 3. 执行 SQL

```sql
-- UPDATE（已有记录）
UPDATE qianniu.qianniu_fliggy_shop_daily_key_data SET
  pingxiaobao_cost = ?, pingxiaobao_imp = ?, pingxiaobao_click = ?,
  tmall_express_cost = ?, tmall_express_imp = ?, tmall_express_click = ?,
  gravity_rubiks_cube_cost = ?, gravity_rubiks_cube_imp = ?, gravity_rubiks_cube_click = ?,
  mansa_dae_cost = ?, mansa_dae_views = ?, mansa_dae_click = ?,
  cost_total = ?, imp_total = ?, click_total = ?
WHERE 日期 = ?;

-- INSERT（无记录）
INSERT INTO qianniu.qianniu_fliggy_shop_daily_key_data (日期, pingxiaobao_cost, pingxiaobao_imp, pingxiaobao_click, tmall_express_cost, tmall_express_imp, tmall_express_click, gravity_rubiks_cube_cost, gravity_rubiks_cube_imp, gravity_rubiks_cube_click, mansa_dae_cost, mansa_dae_views, mansa_dae_click, cost_total, imp_total, click_total)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
```

### 4. 验证并返回

```sql
SELECT 日期,
  pingxiaobao_cost, pingxiaobao_imp, pingxiaobao_click,
  tmall_express_cost, tmall_express_imp, tmall_express_click,
  gravity_rubiks_cube_cost, gravity_rubiks_cube_imp, gravity_rubiks_cube_click,
  mansa_dae_cost, mansa_dae_views, mansa_dae_click,
  cost_total, imp_total, click_total
FROM qianniu.qianniu_fliggy_shop_daily_key_data WHERE 日期 = ?;
```

返回格式化的表格给用户确认。

## MySQL 连接信息
- HOST=localhost（⚠️ 必须用 localhost，不要用 IP）
- PORT=3306
- USER=remote_user
- PASS=Tourism2024
- 数据库：qianniu
- 表：qianniu_fliggy_shop_daily_key_data
- 执行方式：`wsl bash -c "mysql -hlocalhost ..."`

## 错误处理
- Excel 中找不到指定日期 → 告诉用户该日期无数据
- MySQL 连不上 → 检查是否在 WSL 中用 localhost
- 找不到 Excel 文件 → 让用户重新发送阿里妈妈 Excel

## 注意事项
- SQL 文件写到 workspace 下执行，不要用 PowerShell 传递多行 SQL
- Python 用 `C:\Users\Gzk\AppData\Local\Programs\Python\Python312\python.exe`
- 万象台的 IMP 字段在 MySQL 中叫 `mansa_dae_views`，不是 `mansa_dae_imp`

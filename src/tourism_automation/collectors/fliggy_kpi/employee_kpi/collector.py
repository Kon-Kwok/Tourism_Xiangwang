"""飞猪客服KPI采集器"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import subprocess
import json

from tourism_automation.collectors.fliggy_kpi.employee_kpi.client import EmployeeKpiClient
from tourism_automation.collectors.fliggy_kpi.employee_kpi.normalize import normalize_employee_kpi_data
from tourism_automation.shared.chrome_cdp_script import resolve_chrome_cdp_script


@dataclass
class EmployeeKpiCollector:
    """员工KPI数据采集器"""
    http = None

    def collect(
        self,
        biz_date: str,
        shop_name: str = "default",
        kpi_id: str = "1721",
        wwt: str = "ALL"
    ) -> Dict[str, object]:
        """采集员工KPI数据

        Args:
            biz_date: 业务日期，格式 "2026-04-19"
            shop_name: 店铺名称
            kpi_id: KPI模板ID
            wwt: 时间范围类型

        Returns:
            Dict: 包含summary和metrics的字典
        """
        client = EmployeeKpiClient(http=self.http)

        # 获取原始数据
        raw_data = self._fetch_data_via_cdp(biz_date, kpi_id, wwt)

        # 规范化数据
        normalized_data = normalize_employee_kpi_data(
            raw_data,
            biz_date,
            shop_name
        )

        return {
            "summary": {
                "metric_source": "cdp_extraction",
                "shop_name": shop_name,
                "page_code": "employee_kpi",
                "collection_date": biz_date,
                "kpi_id": kpi_id,
                "employee_count": len(normalized_data)
            },
            "metrics": [item.to_dict() for item in normalized_data],
            "raw_data": {
                "table_rows": raw_data
            }
        }

    def _fetch_data_via_cdp(
        self,
        date: str,
        kpi_id: str,
        wwt: str
    ) -> List[List[str]]:
        """通过CDP从页面获取表格数据

        Args:
            date: 业务日期
            kpi_id: KPI模板ID
            wwt: 时间范围类型

        Returns:
            List[List[str]]: 表格行数据
        """
        try:
            # 构建页面URL
            page_url = f"https://kf.topchitu.com/web/custom-kpi/employee-kpi?id={kpi_id}&wwt={wwt}"

            # 查找Chrome标签页
            cdp_path = resolve_chrome_cdp_script()

            # 列出所有标签页，找到目标页面
            result = subprocess.run(
                [cdp_path, "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            target_id = None
            for line in result.stdout.split('\n'):
                if 'custom-kpi/employee-kpi' in line or kpi_id in line:
                    # 提取target ID（第一个空格前的字符串）
                    target_id = line.split()[0]
                    break

            if not target_id:
                raise Exception(f"未找到目标页面: {page_url}")

            # 提取表格数据
            js_code = '''
(() => {
    const rows = [];
    const tableRows = document.querySelectorAll("tbody.ant-table-tbody tr");

    tableRows.forEach((row) => {
        const cells = row.querySelectorAll("td");
        const rowData = [];
        cells.forEach(cell => {
            rowData.push(cell.textContent.trim());
        });
        rows.push(rowData);
    });

    return JSON.stringify(rows);
})()
'''

            result = subprocess.run(
                [cdp_path, "eval", target_id, js_code],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise Exception(f"CDP执行失败: {result.stderr}")

            # 解析JSON数据
            table_data = json.loads(result.stdout.strip())

            return table_data

        except subprocess.TimeoutExpired:
            raise Exception("CDP执行超时")
        except json.JSONDecodeError as e:
            raise Exception(f"解析CDP响应失败: {e}")
        except Exception as e:
            raise Exception(f"CDP数据提取失败: {e}")

    def export(
        self,
        biz_date: str,
        password: str = "1234",
        kpi_id: str = "1721",
        wwt: str = "ALL",
        output_dir: str = "/tmp"
    ) -> Dict[str, object]:
        """导出员工KPI数据文件

        通过CDP点击导出按钮，输入密码，并下载文件

        Args:
            biz_date: 业务日期
            password: 导出密码，默认1234
            kpi_id: KPI模板ID
            wwt: 时间范围类型
            output_dir: 输出目录

        Returns:
            Dict: 包含导出结果信息
        """
        import time
        import os

        cdp_path = resolve_chrome_cdp_script()

        try:
            # 1. 列出标签页，找到目标页面
            result = subprocess.run(
                [cdp_path, "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            target_id = None
            for line in result.stdout.split('\n'):
                if 'custom-kpi/employee-kpi' in line or kpi_id in line:
                    target_id = line.split()[0]
                    break

            if not target_id:
                raise Exception(f"未找到目标页面，请先打开: https://kf.topchitu.com/web/custom-kpi/employee-kpi?id={kpi_id}")

            # 2. 点击导出按钮
            print("正在点击导出按钮...")
            click_js = '''
(() => {
    const buttons = document.querySelectorAll(".download___7ocOy");
    if (buttons.length > 0) {
        buttons[0].click();
        return "clicked";
    }
    return "not_found";
})()
'''

            result = subprocess.run(
                [cdp_path, "eval", target_id, click_js],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "clicked" not in result.stdout:
                raise Exception("未找到导出按钮")

            print("✓ 导出按钮已点击")

            # 3. 等待密码输入框出现并输入密码
            time.sleep(1)  # 等待弹窗出现

            print("正在输入密码...")
            password_js = f'''
(() => {{
    // 查找密码输入框
    const inputs = document.querySelectorAll("input[type=\"password\"]");
    if (inputs.length > 0) {{
        inputs[0].value = "{password}";
        inputs[0].dispatchEvent(new Event("input", {{ bubbles: true }}));
        inputs[0].dispatchEvent(new Event("change", {{ bubbles: true }}));

        // 查找确认按钮
        const buttons = document.querySelectorAll("button");
        for (let btn of buttons) {{
            if (btn.textContent.includes("确定") || btn.textContent.includes("确认")) {{
                btn.click();
                return "password_submitted";
            }}
        }}
        return "confirm_button_not_found";
    }}
    return "password_input_not_found";
}})()
'''

            result = subprocess.run(
                [cdp_path, "eval", target_id, password_js],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "password_submitted" in result.stdout:
                print("✓ 密码已输入，等待文件下载...")
            else:
                print(f"提示: {result.stdout}")

            # 4. 等待下载完成
            time.sleep(3)

            # 5. 查找下载的文件
            print("正在查找下载的文件...")

            # 检查常见的下载目录
            download_dirs = [
                os.path.expanduser("~/Downloads"),
                "/tmp",
                output_dir
            ]

            downloaded_files = []
            for dir_path in download_dirs:
                if os.path.exists(dir_path):
                    # 查找最近修改的Excel文件
                    files = []
                    for f in os.listdir(dir_path):
                        if f.endswith(('.xlsx', '.xls', '.csv')):
                            file_path = os.path.join(dir_path, f)
                            mtime = os.path.getmtime(file_path)
                            files.append((mtime, file_path))

                    # 找最近1分钟内修改的文件
                    recent_time = time.time() - 60
                    recent_files = [f for mtime, f in files if mtime > recent_time]
                    downloaded_files.extend(recent_files)

            if downloaded_files:
                # 返回最新的文件
                latest_file = max(downloaded_files, key=lambda f: os.path.getmtime(f))
                file_size = os.path.getsize(latest_file)

                return {
                    "status": "success",
                    "message": "文件导出成功",
                    "file_path": latest_file,
                    "file_size": file_size,
                    "biz_date": biz_date,
                    "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    "status": "success",
                    "message": "导出命令已执行，请检查浏览器下载目录",
                    "biz_date": biz_date,
                    "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "note": "文件可能在浏览器默认下载目录中"
                }

        except subprocess.TimeoutExpired:
            raise Exception("CDP执行超时")
        except Exception as e:
            raise Exception(f"导出失败: {e}")

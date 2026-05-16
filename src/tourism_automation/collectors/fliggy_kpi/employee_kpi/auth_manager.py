"""认证管理器 - 获取和保存浏览器认证信息"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Dict, Optional
import time

from tourism_automation.shared.chrome_cdp_script import resolve_chrome_cdp_script


class AuthManager:
    """认证管理器"""

    def __init__(self, cache_dir: str = "/tmp"):
        self.cache_file = Path(cache_dir) / "fliggy_kpi_auth.json"
        self.cdp_path = resolve_chrome_cdp_script()

    def get_auth_info(self, force_refresh: bool = False) -> Dict:
        """获取认证信息

        Args:
            force_refresh: 是否强制刷新

        Returns:
            Dict: 认证信息（cookies, headers等）
        """
        # 检查缓存的认证信息
        if not force_refresh and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cached = json.load(f)
                    # 检查是否过期（1小时）
                    if time.time() - cached.get('timestamp', 0) < 3600:
                        return cached
            except Exception:
                pass

        # 从浏览器获取新的认证信息
        return self._fetch_auth_from_browser()

    def _fetch_auth_from_browser(self) -> Dict:
        """从浏览器获取认证信息"""
        target_id = self._find_target_page()

        # 获取cookies
        js_code = '''
(() => {
  // 获取document.cookie
  const docCookies = document.cookie;

  // 尝试获取localStorage中的关键信息
  const localStorageData = {};
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key.includes('umId') || key.includes('token') || key.includes('session')) {
      localStorageData[key] = localStorage.getItem(key);
    }
  }

  // 获取所有headers（通过fetch一个请求获取）
  return JSON.stringify({
    cookies: docCookies,
    localStorage: localStorageData,
    userAgent: navigator.userAgent
  });
})()
'''

        result = subprocess.run(
            [self.cdp_path, "eval", target_id, js_code],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            raise Exception(f"获取认证信息失败: {result.stderr}")

        auth_info = json.loads(result.stdout.strip())
        auth_info['timestamp'] = time.time()

        # 保存到文件
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(auth_info, f, indent=2)

        return auth_info

    def _find_target_page(self) -> str:
        """查找Chrome中的KPI页面"""
        result = subprocess.run(
            [self.cdp_path, "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        for line in result.stdout.split('\n'):
            if 'custom-kpi/employee-kpi' in line:
                return line.split()[0]

        raise Exception("未找到目标页面，请先打开: https://kf.topchitu.com/web/custom-kpi/employee-kpi?id=1721")

    def clear_cache(self):
        """清除缓存的认证信息"""
        if self.cache_file.exists():
            self.cache_file.unlink()

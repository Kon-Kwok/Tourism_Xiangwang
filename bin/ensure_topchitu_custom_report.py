#!/usr/bin/env python3
"""Keep Topchitu on the required custom KPI report page after login redirects."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
import urllib.request

import websockets


DEFAULT_TARGET_URL = "https://kf.topchitu.com/web/custom-kpi/employee-kpi?id=1721&wwt=ALL"
TOPCHITU_HOST = "kf.topchitu.com"


def list_tabs(debug_port: int) -> list[dict]:
    with urllib.request.urlopen(f"http://localhost:{debug_port}/json", timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


async def navigate(ws_url: str, target_url: str) -> None:
    async with websockets.connect(ws_url) as ws:
        command = {
            "id": 1,
            "method": "Page.navigate",
            "params": {"url": target_url},
        }
        await ws.send(json.dumps(command))
        await ws.recv()


def ensure_target_tab(debug_port: int, target_url: str) -> bool:
    tabs = [tab for tab in list_tabs(debug_port) if tab.get("type") == "page"]
    target_tabs = [tab for tab in tabs if target_url in tab.get("url", "")]
    if target_tabs:
        return True

    topchitu_tabs = [tab for tab in tabs if TOPCHITU_HOST in tab.get("url", "")]
    if not topchitu_tabs:
        return False

    # Reuse the first Topchitu tab so login/session state stays in one place.
    tab = topchitu_tabs[0]
    asyncio.run(navigate(tab["webSocketDebuggerUrl"], target_url))
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug-port", type=int, default=9222)
    parser.add_argument("--target-url", default=DEFAULT_TARGET_URL)
    parser.add_argument("--watch-seconds", type=int, default=180)
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()

    deadline = time.monotonic() + args.watch_seconds
    while time.monotonic() <= deadline:
        try:
            if ensure_target_tab(args.debug_port, args.target_url):
                return 0
        except Exception:
            # Chrome may still be starting or Topchitu may still be redirecting.
            pass
        time.sleep(args.interval)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

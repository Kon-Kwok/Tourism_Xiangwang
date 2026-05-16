"""Helpers for locating the optional chrome-cdp skill script."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_chrome_cdp_script() -> str:
    configured = os.environ.get("CHROME_CDP_SCRIPT")
    candidates = [
        Path(configured).expanduser() if configured else None,
        Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser() / "skills/chrome-cdp/scripts/cdp.mjs",
        Path("~/.claude/skills/chrome-cdp/scripts/cdp.mjs").expanduser(),
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return str(candidate)
    return str(candidates[1])

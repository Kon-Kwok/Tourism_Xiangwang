#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    config: dict[str, str] = {}
    if not path.exists():
        return config

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        config[key.strip()] = value.strip().strip("'\"")
    return config


def _mysql_command(config: dict[str, str]) -> list[str]:
    command = ["mysql"]
    if config.get("MYSQL_HOST"):
        command.append(f"--host={config['MYSQL_HOST']}")
    if config.get("MYSQL_PORT"):
        command.append(f"--port={config['MYSQL_PORT']}")
    if config.get("MYSQL_USER"):
        command.append(f"--user={config['MYSQL_USER']}")
    if config.get("MYSQL_DATABASE"):
        command.append(config["MYSQL_DATABASE"])
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute SQL from stdin with mysql client settings from env file.")
    parser.add_argument("--env-file", type=Path, default=Path(".env.local"))
    args = parser.parse_args(argv)

    config = load_env_file(args.env_file)
    env = os.environ.copy()
    if config.get("MYSQL_PASSWORD"):
        env["MYSQL_PWD"] = config["MYSQL_PASSWORD"]

    result = subprocess.run(
        _mysql_command(config),
        input=sys.stdin.read(),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    sys.stdout.write(result.stdout)
    sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

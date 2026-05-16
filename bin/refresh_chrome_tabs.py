#!/usr/bin/env python3
"""Refresh selected Chrome tabs through the DevTools protocol."""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time
from datetime import datetime
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen


DEFAULT_DOMAINS = (
    "sycm.taobao.com",
    "fsc.fliggy.com",
    "kf.topchitu.com",
    "brandsearch.taobao.com",
    "branding.taobao.com",
    "one.alimama.com",
)


def log(message: str) -> None:
    timestamp = datetime.now().isoformat(timespec="seconds")
    print(f"{timestamp} {message}", flush=True)


def claim_pid_file(path: str | None) -> None:
    if not path:
        return

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = handle.read().strip()
        if existing:
            try:
                os.kill(int(existing), 0)
            except ProcessLookupError:
                os.unlink(path)
            except ValueError:
                os.unlink(path)
            else:
                raise SystemExit(f"refresh daemon is already running: pid {existing}")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))

    def cleanup() -> None:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                current = handle.read().strip()
            if current == str(os.getpid()):
                os.unlink(path)
        except FileNotFoundError:
            pass

    atexit.register(cleanup)


def fetch_targets(port: int, timeout: float) -> list[dict]:
    with urlopen(f"http://127.0.0.1:{port}/json", timeout=timeout) as response:
        return json.load(response)


def should_refresh(target: dict, domains: tuple[str, ...]) -> bool:
    if target.get("type") != "page":
        return False

    url = target.get("url") or ""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError("websocket closed while reading")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def websocket_frame(payload: str) -> bytes:
    data = payload.encode("utf-8")
    header = bytearray([0x81])
    if len(data) < 126:
        header.append(0x80 | len(data))
    elif len(data) <= 0xFFFF:
        header.append(0x80 | 126)
        header.extend(struct.pack(">H", len(data)))
    else:
        header.append(0x80 | 127)
        header.extend(struct.pack(">Q", len(data)))

    mask = os.urandom(4)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
    return bytes(header) + mask + masked


def read_ws_message(sock: socket.socket) -> str:
    first, second = recv_exact(sock, 2)
    opcode = first & 0x0F
    length = second & 0x7F
    if length == 126:
        length = struct.unpack(">H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", recv_exact(sock, 8))[0]

    mask = recv_exact(sock, 4) if second & 0x80 else b""
    payload = recv_exact(sock, length) if length else b""
    if mask:
        payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))

    if opcode == 8:
        raise ConnectionError("websocket closed by server")
    if opcode not in {1, 2}:
        return ""
    return payload.decode("utf-8", errors="replace")


def send_cdp_message(ws_url: str, message: dict, timeout: float) -> None:
    parsed = urlparse(ws_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"

    key = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).encode("ascii")

    expected_accept = base64.b64encode(
        hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
    ).decode("ascii")

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)

        response = b""
        while b"\r\n\r\n" not in response:
            response += sock.recv(4096)
            if not response:
                raise ConnectionError("empty websocket handshake response")

        headers = response.decode("iso-8859-1", errors="replace")
        if " 101 " not in headers or expected_accept not in headers:
            raise ConnectionError("websocket handshake failed")

        sock.sendall(websocket_frame(json.dumps(message, separators=(",", ":"))))
        read_ws_message(sock)


def refresh_once(port: int, domains: tuple[str, ...], timeout: float) -> int:
    targets = fetch_targets(port, timeout)
    matched = [target for target in targets if should_refresh(target, domains)]
    if not matched:
        log("no matching business tabs found")
        return 0

    refreshed = 0
    for target in matched:
        title = target.get("title") or "(untitled)"
        url = target.get("url") or ""
        ws_url = target.get("webSocketDebuggerUrl")
        if not ws_url:
            log(f"skip tab without websocket: {url}")
            continue
        try:
            send_cdp_message(
                ws_url,
                {"id": 1, "method": "Page.reload", "params": {"ignoreCache": False}},
                timeout,
            )
        except Exception as exc:  # noqa: BLE001 - daemon should keep refreshing other tabs.
            log(f"refresh failed: {title} {url} ({exc})")
            continue
        refreshed += 1
        log(f"refreshed: {title} {url}")
    return refreshed


def parse_domains(value: str) -> tuple[str, ...]:
    domains = tuple(item.strip() for item in value.split(",") if item.strip())
    if not domains:
        raise argparse.ArgumentTypeError("at least one domain is required")
    return domains


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=9222, help="Chrome debug port")
    parser.add_argument("--interval", type=int, default=1800, help="Refresh interval in seconds")
    parser.add_argument("--initial-delay", type=int, default=0, help="Delay before first refresh")
    parser.add_argument(
        "--domains",
        type=parse_domains,
        default=DEFAULT_DOMAINS,
        help="Comma-separated hostnames to refresh",
    )
    parser.add_argument("--pid-file", help="PID file used to avoid duplicate daemons")
    parser.add_argument("--timeout", type=float, default=8.0, help="HTTP/CDP timeout in seconds")
    parser.add_argument("--once", action="store_true", help="Refresh once and exit")
    args = parser.parse_args()

    claim_pid_file(args.pid_file)

    if args.once:
        try:
            refreshed = refresh_once(args.port, args.domains, args.timeout)
        except (ConnectionError, OSError, URLError) as exc:
            log(f"chrome debug port unavailable: {exc}")
            return 1
        log(f"done: refreshed {refreshed} tab(s)")
        return 0

    log(
        "refresh daemon started: "
        f"port={args.port} interval={args.interval}s domains={','.join(args.domains)}"
    )
    if args.initial_delay > 0:
        log(f"waiting initial delay: {args.initial_delay}s")
        time.sleep(args.initial_delay)

    while True:
        try:
            refreshed = refresh_once(args.port, args.domains, args.timeout)
            log(f"cycle complete: refreshed {refreshed} tab(s)")
        except (ConnectionError, OSError, URLError) as exc:
            log(f"chrome debug port unavailable: {exc}")
        except Exception as exc:  # noqa: BLE001 - keep the daemon alive.
            log(f"unexpected refresh error: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())

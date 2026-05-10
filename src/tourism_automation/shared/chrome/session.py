"""HTTP collection using the local Chrome login state."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from pathlib import Path
from typing import Dict

import requests
import secretstorage
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from tourism_automation.shared.http.json_client import JsonHttpClient


CHROME_COOKIE_DB = Path.home() / ".config/google-chrome-debug/Default/Cookies"
CHROME_SAFE_STORAGE_LABEL = "Chrome Safe Storage"
CHROME_COOKIE_HOST_KEYS = (
    ".alimama.com",
    "sycm.taobao.com",
    "brandsearch.taobao.com",
    "branding.taobao.com",
    "one.alimama.com",
    "club.alimama.com",
    "bpcommon.alimama.com",
    "ai.alimama.com",
    "pass.alimama.com",
    ".taobao.com",
    ".fliggy.com",
    "fsc.fliggy.com",
    "sell.fliggy.com",
    "seller.fliggy.com",
)


@dataclass
class ChromeHttpClient:
    session: requests.Session

    @classmethod
    def from_local_chrome(cls) -> "ChromeHttpClient":
        return cls(session=build_chrome_session())

    def fetch_json(self, url: str, referer: str) -> Dict[str, object]:
        absolute_url = url if url.startswith("http") else f"https://sycm.taobao.com{url}"
        return JsonHttpClient(self.session).fetch_json(absolute_url, referer=referer)


def build_chrome_session() -> requests.Session:
    if not CHROME_COOKIE_DB.exists():
        raise RuntimeError(f"Chrome cookie database not found: {CHROME_COOKIE_DB}")

    session = requests.Session()
    db_version = _read_cookie_db_version(CHROME_COOKIE_DB)
    host_hash_len = 32 if db_version >= 24 else 0
    chrome_secret = _read_chrome_safe_storage_secret()
    key = pbkdf2_hmac("sha1", chrome_secret.encode("utf-8"), b"saltysalt", 1, 16)

    conn = sqlite3.connect(f"file:{CHROME_COOKIE_DB}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        host_keys_sql = ", ".join(f"'{host_key}'" for host_key in CHROME_COOKIE_HOST_KEYS)
        cursor.execute(
            f"""
            SELECT host_key, name, value, encrypted_value, path
            FROM cookies
            WHERE host_key IN ({host_keys_sql})
            """
        )
        for host_key, name, value, encrypted_value, path in cursor.fetchall():
            cookie_value = value or _decrypt_cookie_value(
                encrypted_value=encrypted_value,
                key=key,
                host_hash_len=host_hash_len,
            )
            if not cookie_value:
                continue
            if not _is_http_header_value(cookie_value):
                continue
            session.cookies.set(
                name,
                cookie_value,
                domain=host_key.lstrip("."),
                path=path,
            )
    finally:
        conn.close()

    return session


def _read_cookie_db_version(cookie_db: Path) -> int:
    conn = sqlite3.connect(f"file:{cookie_db}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM meta WHERE key="version"')
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    finally:
        conn.close()


def _read_chrome_safe_storage_secret() -> str:
    bus = secretstorage.dbus_init()
    collection = secretstorage.get_default_collection(bus)
    for item in collection.get_all_items():
        if item.get_label() == CHROME_SAFE_STORAGE_LABEL:
            return item.get_secret().decode("utf-8")
    raise RuntimeError(f"Secret Service item not found: {CHROME_SAFE_STORAGE_LABEL}")


def _decrypt_cookie_value(*, encrypted_value: bytes, key: bytes, host_hash_len: int) -> str:
    if not encrypted_value:
        return ""
    if encrypted_value.startswith((b"v10", b"v11")):
        cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16))
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_value[3:]) + decryptor.finalize()
        decrypted = decrypted[: -decrypted[-1]]
        if host_hash_len and len(decrypted) > host_hash_len:
            decrypted = decrypted[host_hash_len:]
        return decrypted.decode("utf-8", errors="ignore")
    return encrypted_value.decode("utf-8", errors="ignore")


def _is_http_header_value(value: str) -> bool:
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        return False
    return True

#!/usr/bin/env python3

from __future__ import annotations

import secrets
from pathlib import Path


def ensure_secret(path: Path, label: str) -> None:
    if path.exists():
        current = path.read_text(encoding="utf-8").strip()
        if current:
            print(f"{label}: keep existing")
            return

    path.parent.mkdir(parents=True, exist_ok=True)
    # Relay treats secrets as raw strings for JWT HS256 and HMAC-SHA256.
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="utf-8")
    print(f"{label}: generated")


def main() -> int:
    base = Path("tmp/e2e/relay/config/secrets")
    ensure_secret(base / "jwt_secret_key.txt", "jwt_secret_key.txt")
    ensure_secret(base / "mac_secret_key.txt", "mac_secret_key.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

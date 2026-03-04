#!/usr/bin/env python3

from __future__ import annotations

import re
import sys


def normalize_privkey(key: str) -> str:
    k = key.strip()
    if not k.startswith("0x"):
        k = "0x" + k
    if not re.fullmatch(r"0x[0-9a-fA-F]{64}", k):
        raise ValueError("Invalid private key format, expected 0x + 64 hex chars")
    return k


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/get-address.py <private_key>", file=sys.stderr)
        return 1

    key = normalize_privkey(sys.argv[1])
    try:
        from eth_account import Account
    except Exception as exc:
        raise RuntimeError(
            "Missing dependency: eth-account. Install with: pip install eth-account"
        ) from exc

    print(Account.from_key(key).address)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

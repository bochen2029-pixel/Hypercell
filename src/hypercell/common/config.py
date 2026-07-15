"""Minimal .env loader (stdlib; no dependency). Existing environment variables always win.

Keys live in a gitignored `.env` at the repo root (see `.env.example`). Loaded once at CLI/API startup.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_env(path: str | Path = ".env") -> int:
    """Populate os.environ from a KEY=VALUE file without overwriting existing vars. Returns count set."""
    p = Path(path)
    if not p.exists():
        return 0
    n = 0
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val
            n += 1
    return n

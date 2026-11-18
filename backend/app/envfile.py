"""Pembaca .env sederhana untuk jalur manual (tanpa Docker). Nilai yang sudah ada di environment tidak ditimpa."""
import os
from pathlib import Path

_CANDIDATES = [Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[1] / ".env"]


def load_env() -> None:
    for path in _CANDIDATES:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

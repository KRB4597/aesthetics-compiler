from __future__ import annotations
import hashlib
from pathlib import Path


def load_text(source: str | Path) -> tuple[str, str]:
    p = Path(source)
    if p.exists():
        text = p.read_text(encoding="utf-8")
    else:
        text = str(source)
    sha = hashlib.sha256(text.encode()).hexdigest()
    return text, sha

from __future__ import annotations
import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


class _StyleExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[dict[str, Any]] = []
        self.styles: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        style = attr_dict.get("style", "") or ""
        klass = attr_dict.get("class", "") or ""
        self.elements.append({
            "tag": tag,
            "style": style,
            "class": klass,
            "depth": self._depth,
        })
        self._depth += 1

    def handle_endtag(self, _tag: str) -> None:
        self._depth = max(0, self._depth - 1)

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if stripped.startswith("<style") or "color" in stripped or "background" in stripped:
            self.styles.append(stripped)


def load_html(source: str | Path) -> tuple[str, dict[str, Any], str]:
    """Return (raw_html, metadata, sha256)."""
    p = Path(source)
    if p.exists():
        raw = p.read_text(encoding="utf-8")
    else:
        raw = str(source)

    sha = hashlib.sha256(raw.encode()).hexdigest()

    parser = _StyleExtractor()
    parser.feed(raw)

    colors: list[str] = _extract_colors(raw)
    background_colors: list[str] = _extract_background_colors(raw)
    font_families: list[str] = _extract_fonts(raw)

    meta: dict[str, Any] = {
        "raw": raw,
        "elements": parser.elements,
        "css_colors": colors,
        "background_colors": background_colors,
        "font_families": font_families,
        "element_count": len(parser.elements),
        "max_depth": max((e["depth"] for e in parser.elements), default=0),
    }
    return raw, meta, sha


_COLOR_RE = re.compile(
    r"(?:color|fill|stroke)\s*:\s*(#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|[a-zA-Z]+)",
    re.IGNORECASE,
)
_BG_COLOR_RE = re.compile(
    r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8}|rgb\([^)]+\)|[a-zA-Z]+)",
    re.IGNORECASE,
)
_FONT_RE = re.compile(r"font-family\s*:\s*([^;\"'<>]+)", re.IGNORECASE)


def _extract_colors(html: str) -> list[str]:
    return list(dict.fromkeys(_COLOR_RE.findall(html)))[:20]


def _extract_background_colors(html: str) -> list[str]:
    return list(dict.fromkeys(_BG_COLOR_RE.findall(html)))[:10]


def _extract_fonts(html: str) -> list[str]:
    return list(dict.fromkeys(f.strip().strip("'\"") for f in _FONT_RE.findall(html)))[:10]

"""Dataset loading for the aesthetics benchmark.

Primary target: **AADB** (Aesthetics with Attributes Database, Kong et al.,
ECCV 2016) — 10,000 photos, each with an overall aesthetic score and 11
human-annotated attribute scores.  Several of those attributes line up almost
1:1 with this compiler's dimensions, which is what makes AADB a good yardstick.

AADB is not redistributable here, so this module does two things:

1. ``load_labeled_images(csv_path)`` reads a CSV *you* provide once you have the
   data.  Expected columns (header row required):

       image,overall,balancing_element,color_harmony,symmetry,repetition,vivid_color

   ``image`` is a path (absolute, or relative to the CSV).  ``overall`` is the
   mean human aesthetic score.  The attribute columns are optional — include
   whichever ones you have; the runner only correlates the ones present.

2. ``ensure_sample()`` generates a tiny, self-contained sample (six synthetic
   images + a label CSV) so the harness runs out-of-the-box with no download.
   The sample exists to prove the pipeline works end-to-end; the correlation
   numbers it produces are NOT meaningful — supply real AADB for that.

See ``benchmarks/README.md`` for how to obtain AADB and build the CSV.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

# Compiler-dimension  ->  AADB attribute column.  Only these are correlated.
ATTRIBUTE_MAP: dict[str, str] = {
    "balance": "balancing_element",
    "color_harmony": "color_harmony",
    "order": "symmetry",
    "rhythm": "repetition",
    "saturation": "vivid_color",
}

_SAMPLE_DIR = Path(__file__).parent / "sample_data"
_SAMPLE_IMAGES = _SAMPLE_DIR / "images"
_SAMPLE_CSV = _SAMPLE_DIR / "aadb_sample.csv"


@dataclass
class LabeledImage:
    """One image plus its human labels."""
    image: Path
    overall: float | None = None
    attributes: dict[str, float] = field(default_factory=dict)


def load_labeled_images(csv_path: str | Path) -> list[LabeledImage]:
    """Load (image, overall, attributes) rows from a CSV.

    Image paths are resolved relative to the CSV file's directory if not
    absolute.  Missing/blank cells are skipped (not treated as 0).
    """
    csv_path = Path(csv_path)
    base = csv_path.parent
    rows: list[LabeledImage] = []
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        attr_cols = set(ATTRIBUTE_MAP.values())
        for row in reader:
            img = Path(row["image"])
            if not img.is_absolute():
                img = (base / img).resolve()
            overall = _to_float(row.get("overall"))
            attrs = {
                col: _to_float(row[col])
                for col in attr_cols
                if col in row and _to_float(row[col]) is not None
            }
            rows.append(LabeledImage(image=img, overall=overall, attributes=attrs))
    return rows


def _to_float(v) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def ensure_sample() -> Path:
    """Create the bundled synthetic sample if missing; return the CSV path.

    Requires Pillow (already a core dependency of aesthetics-compiler).
    """
    if _SAMPLE_CSV.exists():
        return _SAMPLE_CSV

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - Pillow is a core dep
        raise RuntimeError(
            "Pillow is required to generate the benchmark sample images. "
            "Install the project first: pip install -e ."
        ) from exc

    _SAMPLE_IMAGES.mkdir(parents=True, exist_ok=True)
    S = 96  # small images keep the sample fast and tiny

    # Each entry: (filename, pixel-generator, plausible stand-in human labels).
    # NOTE: these labels are illustrative only — they make the harness runnable,
    # they are not real human judgements.
    def _checker(x, y):
        return (230, 230, 230) if ((x // 12) + (y // 12)) % 2 else (25, 25, 25)

    def _v_gradient(x, y):
        t = y / S
        return (int(40 + 160 * t), int(60 + 120 * t), int(180 - 80 * t))

    def _noise(x, y):
        n = (x * 1103515245 + y * 12345 + x * y) % 256  # deterministic pseudo-noise
        return (n, (n * 37) % 256, (n * 89) % 256)

    def _solid(x, y):
        return (70, 130, 180)

    def _concentric(x, y):
        cx, cy = S / 2, S / 2
        r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        return (200, 80, 80) if int(r // 8) % 2 else (250, 240, 220)

    def _split(x, y):
        return (240, 30, 30) if x < S / 2 else (30, 30, 240)

    specs = [
        ("checker.png",    _checker,    dict(overall=0.62, balancing_element=0.7, color_harmony=0.4, symmetry=0.9,  repetition=0.8, vivid_color=0.2)),
        ("gradient.png",   _v_gradient, dict(overall=0.55, balancing_element=0.5, color_harmony=0.7, symmetry=0.3,  repetition=0.2, vivid_color=0.6)),
        ("noise.png",      _noise,      dict(overall=0.20, balancing_element=0.3, color_harmony=0.1, symmetry=0.1,  repetition=0.2, vivid_color=0.7)),
        ("solid.png",      _solid,      dict(overall=0.40, balancing_element=0.6, color_harmony=0.6, symmetry=0.5,  repetition=0.1, vivid_color=0.5)),
        ("concentric.png", _concentric, dict(overall=0.66, balancing_element=0.8, color_harmony=0.5, symmetry=0.85, repetition=0.7, vivid_color=0.5)),
        ("split.png",      _split,      dict(overall=0.45, balancing_element=0.5, color_harmony=0.3, symmetry=0.6,  repetition=0.1, vivid_color=0.85)),
    ]

    fieldnames = ["image", "overall", *ATTRIBUTE_MAP.values()]
    with _SAMPLE_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for name, gen, labels in specs:
            path = _SAMPLE_IMAGES / name
            img = Image.new("RGB", (S, S))
            img.putdata([gen(x, y) for y in range(S) for x in range(S)])
            img.save(path)
            row = {"image": f"images/{name}"}
            row.update(labels)
            writer.writerow(row)

    return _SAMPLE_CSV

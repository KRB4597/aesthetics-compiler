from __future__ import annotations
import hashlib
import math
from pathlib import Path
from typing import Any


def load_image(source: str | Path) -> tuple[Any, dict[str, Any], str]:
    """Return (pil_image, metadata, sha256). Requires Pillow."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError as e:
        raise ImportError("Pillow and numpy are required for image input: pip install Pillow numpy") from e

    p = Path(source)
    img = Image.open(p).convert("RGB")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()

    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape[:2]

    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]

    hsv_h, hsv_s, hsv_v = _rgb_to_hsv_channels(arr)

    is_animated = getattr(img, "n_frames", 1) > 1
    n_frames = getattr(img, "n_frames", 1)
    duration_s = None
    if is_animated:
        try:
            duration_ms = img.info.get("duration", 100) * n_frames
            duration_s = duration_ms / 1000.0
        except Exception:
            duration_s = n_frames / 10.0

    meta: dict[str, Any] = {
        "width": w,
        "height": h,
        "arr": arr,
        "lum": lum,
        "hsv_h": hsv_h,
        "hsv_s": hsv_s,
        "hsv_v": hsv_v,
        "is_animated": is_animated,
        "n_frames": n_frames,
        "duration_s": duration_s,
    }
    return img, meta, sha


def _rgb_to_hsv_channels(arr: "np.ndarray") -> tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
    import numpy as np
    r, g, b = arr[:, :, 0] / 255.0, arr[:, :, 1] / 255.0, arr[:, :, 2] / 255.0
    v = np.maximum(np.maximum(r, g), b)
    s = np.where(v > 0, (v - np.minimum(np.minimum(r, g), b)) / (v + 1e-9), 0.0)
    rc = np.where(v > 0, (v - r) / (v - np.minimum(np.minimum(r, g), b) + 1e-9), 0.0)
    gc = np.where(v > 0, (v - g) / (v - np.minimum(np.minimum(r, g), b) + 1e-9), 0.0)
    bc = np.where(v > 0, (v - b) / (v - np.minimum(np.minimum(r, g), b) + 1e-9), 0.0)
    h = np.where(r == v, bc - gc,
        np.where(g == v, 2.0 + rc - bc,
                 4.0 + gc - rc))
    h = (h / 6.0) % 1.0
    return h, s, v

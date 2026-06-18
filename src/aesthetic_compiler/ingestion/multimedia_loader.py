from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any


def load_multimedia(source: str | Path) -> tuple[list[Any], dict[str, Any], str]:
    """Return (frames, metadata, sha256) where frames is a list of PIL Images.

    For animated GIF uses built-in Pillow. For video formats, attempts to use
    imageio (optional). Falls back to single-frame extraction.
    """
    try:
        from PIL import Image
        import numpy as np
    except ImportError as e:
        raise ImportError("Pillow and numpy are required: pip install Pillow numpy") from e

    p = Path(source)
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    suffix = p.suffix.lower()

    frames: list[Any] = []
    duration_s: float = 0.0
    fps: float = 10.0

    if suffix == ".gif":
        img = Image.open(p)
        try:
            n = getattr(img, "n_frames", 1)
            frame_duration = img.info.get("duration", 100) / 1000.0
            duration_s = n * frame_duration
            fps = 1.0 / max(frame_duration, 0.01)
            sample_indices = _sample_indices(n, max_frames=30)
            for i in sample_indices:
                img.seek(i)
                frames.append(img.convert("RGB").copy())
        except EOFError:
            frames.append(img.convert("RGB").copy())
    else:
        try:
            import imageio
            reader = imageio.get_reader(str(p))
            meta_data = reader.get_meta_data()
            fps = float(meta_data.get("fps", 24))
            n_frames = meta_data.get("nframes", None)
            if n_frames is None:
                all_frames = list(reader)
                n_frames = len(all_frames)
                duration_s = n_frames / fps
                sample_indices = _sample_indices(n_frames, max_frames=30)
                for i in sample_indices:
                    frames.append(Image.fromarray(all_frames[i]).convert("RGB"))
            else:
                duration_s = n_frames / fps
                sample_indices = _sample_indices(n_frames, max_frames=30)
                for i in sample_indices:
                    reader.set_image_index(i)
                    frames.append(Image.fromarray(reader.get_next_data()).convert("RGB"))
            reader.close()
        except ImportError:
            img = Image.open(p).convert("RGB")
            frames = [img]
            fps = 1.0
            duration_s = 1.0

    meta: dict[str, Any] = {
        "fps": fps,
        "duration_s": duration_s,
        "n_frames_sampled": len(frames),
        "suffix": suffix,
    }
    return frames, meta, sha


def _sample_indices(n: int, max_frames: int = 30) -> list[int]:
    if n <= max_frames:
        return list(range(n))
    step = n / max_frames
    return [int(i * step) for i in range(max_frames)]

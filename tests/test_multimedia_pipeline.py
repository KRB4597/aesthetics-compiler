"""Multimedia input-mode tests — multimedia_loader/extractor were 0% covered.

Uses an animated GIF (Pillow, a core dep) and forces ``input_mode='multimedia'``
so the loader's frame-sampling path and the temporal extractor run without
needing imageio or a real video file.

Not covered here: the imageio-based video branch in load_multimedia (lines for
.mp4/.avi/etc.), which needs imageio + a real encoded video.  Documented gap.
"""
import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image  # noqa: E402

from aesthetics_compiler.annotation.multimedia_extractor import MultimediaExtractor  # noqa: E402
from aesthetics_compiler.ingestion.multimedia_loader import (  # noqa: E402
    _sample_indices,
    load_multimedia,
)
from aesthetics_compiler.pipeline.orchestrator import compile_document  # noqa: E402

COLORS = [(20, 20, 20), (220, 40, 30), (30, 80, 190), (230, 200, 40)]


def _make_gif(path, colors=COLORS, size=48, duration=100):
    frames = [Image.new("RGB", (size, size), c) for c in colors]
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration, loop=0)
    return path


def test_multimedia_compiles_end_to_end(tmp_path):
    gif = _make_gif(tmp_path / "clip.gif")
    ir = compile_document(str(gif), input_mode="multimedia", quiet=True)
    assert ir.document.input_mode == "multimedia"
    assert ir.document.medium == "video"
    assert len(ir.elements) >= 1
    assert ir.elements[0].element_type == "frame_region"
    assert ir.audit.graph_hash and len(ir.audit.graph_hash) == 64
    assert set(ir.projections)


def test_multimedia_loader_samples_frames(tmp_path):
    gif = _make_gif(tmp_path / "clip.gif")
    frames, meta, sha = load_multimedia(str(gif))
    assert len(frames) == len(COLORS)
    assert meta["n_frames_sampled"] == len(COLORS)
    assert meta["fps"] > 0
    assert meta["suffix"] == ".gif"
    assert len(sha) == 64


def test_sample_indices_caps_and_spans():
    assert _sample_indices(5, max_frames=30) == list(range(5))
    capped = _sample_indices(100, max_frames=10)
    assert len(capped) == 10
    assert capped[0] == 0
    assert capped[-1] < 100


def test_multimedia_extractor_handles_empty_frames():
    assert MultimediaExtractor().extract([], {}) .elements == []


def test_multimedia_extractor_composites_frames(tmp_path):
    gif = _make_gif(tmp_path / "clip.gif")
    frames, meta, _ = load_multimedia(str(gif))
    result = MultimediaExtractor().extract(frames, meta)
    assert result.medium_hint == "video"
    assert len(result.elements) == 1
    vec = result.elements[0].aesthetic_vector
    # rhythm is a temporal dimension only the multimedia path computes.
    assert 0.0 <= vec.rhythm.value <= 1.0

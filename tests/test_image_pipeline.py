"""Image input-mode smoke test — the image extractor/loader were 0% covered.

Generates a small PNG (Pillow is a core dependency) and runs it through the
full compiler so the IMAGE code path is exercised end-to-end.
"""
import pytest

PIL = pytest.importorskip("PIL")  # Pillow is a core dep; skip cleanly if absent.
from PIL import Image  # noqa: E402

from aesthetics_compiler.pipeline.orchestrator import compile_document  # noqa: E402


def _make_png(path, kind="checker", size=64):
    img = Image.new("RGB", (size, size))
    if kind == "checker":
        px = [((230, 230, 230) if ((x // 8) + (y // 8)) % 2 else (20, 20, 20))
              for y in range(size) for x in range(size)]
    else:  # solid
        px = [(70, 130, 180)] * (size * size)
    img.putdata(px)
    img.save(path)
    return path


def test_image_compiles_end_to_end(tmp_path):
    png = _make_png(tmp_path / "checker.png")
    ir = compile_document(str(png), quiet=True)
    assert ir.document.input_mode == "image"
    assert len(ir.elements) >= 1
    assert ir.audit.graph_hash and len(ir.audit.graph_hash) == 64
    assert set(ir.projections)  # projections ran


def test_image_hash_is_deterministic(tmp_path):
    png = _make_png(tmp_path / "solid.png", kind="solid")
    h1 = compile_document(str(png), quiet=True).audit.graph_hash
    h2 = compile_document(str(png), quiet=True).audit.graph_hash
    assert h1 == h2

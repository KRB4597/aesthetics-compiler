"""HTML input-mode tests — html_loader and html_extractor were 0% covered.

The HTML path is pure stdlib (html.parser + regex), so these run with no extra
dependencies.
"""
from aesthetics_compiler.ingestion.html_loader import load_html
from aesthetics_compiler.pipeline.orchestrator import compile_document

HTML = (
    '<html><body style="background-color:#222222">'
    '<div style="color:#e0e0e0;font-family:Helvetica">A balanced layout</div>'
    '<p style="color:rgb(200,40,30)">Red accent</p>'
    '<span style="color:blue">Blue accent</span>'
    "</body></html>"
)


def test_html_compiles_end_to_end(tmp_path):
    p = tmp_path / "page.html"
    p.write_text(HTML, encoding="utf-8")
    ir = compile_document(str(p), quiet=True)
    assert ir.document.input_mode == "html"
    assert len(ir.elements) >= 1
    assert ir.audit.graph_hash and len(ir.audit.graph_hash) == 64
    assert set(ir.projections)


def test_html_loader_extracts_colors_fonts_structure(tmp_path):
    p = tmp_path / "page.html"
    p.write_text(HTML, encoding="utf-8")
    raw, meta, sha = load_html(str(p))
    assert meta["element_count"] >= 3
    assert meta["max_depth"] >= 1
    assert any("#" in c or "rgb" in c for c in meta["css_colors"])
    assert meta["background_colors"]
    assert any("helvetica" in f.lower() for f in meta["font_families"])
    assert len(sha) == 64


def test_html_loader_accepts_inline_string():
    # Non-existent path falls back to treating the argument as raw HTML.
    raw, meta, sha = load_html('<div style="color:#fff">x</div>')
    assert meta["element_count"] >= 1


def test_html_hash_is_deterministic(tmp_path):
    p = tmp_path / "page.html"
    p.write_text(HTML, encoding="utf-8")
    h1 = compile_document(str(p), quiet=True).audit.graph_hash
    h2 = compile_document(str(p), quiet=True).audit.graph_hash
    assert h1 == h2


STRUCTURAL_HTML = (
    "<html><body>"
    '<header style="color:#ff0000;background-color:#ffffff">Top</header>'
    '<main style="color:#00ff00"><section style="color:#0000ff">body</section></main>'
    '<footer style="color:#00ffff">Bottom</footer>'
    "</body></html>"
)


def test_html_structural_tags_become_dom_nodes(tmp_path):
    p = tmp_path / "structural.html"
    p.write_text(STRUCTURAL_HTML, encoding="utf-8")
    ir = compile_document(str(p), quiet=True)
    tags = {e.metadata.get("tag") for e in ir.elements}
    assert tags & {"header", "main", "section", "footer"}
    assert any(e.element_type == "dom_node" for e in ir.elements)
    # Multiple CSS colors should classify into some color-harmony category.
    assert ir.color_schemes and ir.color_schemes[0].harmony_type


def test_html_high_dom_complexity_emits_fact(tmp_path):
    body = "".join(f'<div style="color:#111111">{i}</div>' for i in range(120))
    p = tmp_path / "big.html"
    p.write_text(f"<html><body>{body}</body></html>", encoding="utf-8")
    ir = compile_document(str(p), quiet=True)
    assert "complexity_overload" in {f.fact_kind for f in ir.aesthetic_facts}

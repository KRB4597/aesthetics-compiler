import pytest
from aesthetic_compiler.pipeline.orchestrator import compile_document
from aesthetic_compiler.tiers import ALL_PROJECTIONS


def test_default_projections(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A vibrant, balanced, symmetrical composition with harmonious colors.")
    ir = compile_document(str(f))
    assert set(ir.projections.keys()) == set(ALL_PROJECTIONS)


def test_single_projection(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A minimal, ordered, monochromatic design.")
    ir = compile_document(str(f), projections=["birkhoff"])
    assert list(ir.projections.keys()) == ["birkhoff"]


def test_subset_projections(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Complex, chaotic, vibrant colors, tense composition.")
    ir = compile_document(str(f), projections=["birkhoff", "berlyne"])
    assert "birkhoff" in ir.projections
    assert "berlyne" in ir.projections
    assert "arnheim" not in ir.projections


def test_invalid_projection(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A painting.")
    with pytest.raises(ValueError, match="Unknown projection"):
        compile_document(str(f), projections=["nonexistent"])


def test_graph_hash_set(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Red rectangles on white background, Mondrian-like.")
    ir = compile_document(str(f))
    assert ir.audit.graph_hash is not None
    assert len(ir.audit.graph_hash) == 64


def test_schema_version(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A Rothko-like color field painting.")
    ir = compile_document(str(f))
    assert ir.schema_version == "aesthetic_ir_v0.1"


def test_audit_passes_recorded(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A landscape painting.")
    ir = compile_document(str(f))
    pass_names = [p.pass_name for p in ir.audit.passes]
    assert "extraction" in pass_names
    assert "am_dag" in pass_names
    assert "projection_evaluation" in pass_names
    assert "harmony_verdict" in pass_names


def test_text_input_mode(tmp_path):
    f = tmp_path / "work.txt"
    f.write_text("Abstract expressionist painting with dynamic tension.")
    ir = compile_document(str(f))
    assert ir.document.input_mode == "text"


def test_title_override(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Some artwork.")
    ir = compile_document(str(f), title="My Custom Title")
    assert ir.document.title == "My Custom Title"


def test_disagreement_field_type(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("A painting.")
    ir = compile_document(str(f))
    assert ir.cross_projection_disagreement is None or isinstance(ir.cross_projection_disagreement, dict)

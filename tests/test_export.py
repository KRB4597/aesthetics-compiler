"""Tests for the Schema.org/VisualArtwork exporter (was 0% covered)."""
import json

from aesthetics_compiler.export.schema_org import export_schema_org
from aesthetics_compiler.ir.schemas import AESTHETIC_DIMENSIONS
from aesthetics_compiler.pipeline.orchestrator import compile_document


def _ir():
    return compile_document(
        "A vibrant Rothko-like oil painting, balanced and harmonious.", quiet=True
    )


def test_schema_org_is_valid_jsonld():
    o = json.loads(export_schema_org(_ir()))
    assert o["@context"] == "https://schema.org"
    assert o["@type"] == "VisualArtwork"
    assert o["name"]


def test_schema_org_exposes_every_dimension():
    o = json.loads(export_schema_org(_ir()))
    names = {p["name"] for p in o["additionalProperty"]}
    for dim in AESTHETIC_DIMENSIONS:
        assert f"aesthetic:{dim}" in names
    assert len(o["additionalProperty"]) == len(AESTHETIC_DIMENSIONS)


def test_schema_org_carries_graph_hash_and_projections():
    ir = _ir()
    o = json.loads(export_schema_org(ir))
    assert o["identifier"]["value"] == ir.audit.graph_hash
    assert set(o["projectionResults"]) == set(ir.projections)


def test_schema_org_property_values_match_ir():
    ir = _ir()
    o = json.loads(export_schema_org(ir))
    by_name = {p["name"]: p for p in o["additionalProperty"]}
    for dim in AESTHETIC_DIMENSIONS:
        ds = getattr(ir.aggregate_aesthetic_vector, dim)
        assert by_name[f"aesthetic:{dim}"]["value"] == round(ds.value, 3)
        assert by_name[f"aesthetic:{dim}"]["description"] == ds.direction


def test_schema_org_writes_file(tmp_path):
    p = tmp_path / "art.jsonld"
    s = export_schema_org(_ir(), p)
    assert p.exists()
    assert json.loads(p.read_text(encoding="utf-8")) == json.loads(s)

from aesthetics_compiler.ir.schemas import (
    AestheticVector, DimensionScore, AESTHETIC_DIMENSIONS,
    _direction, AestheticIR, Document, AuditRecord,
)
from aesthetics_compiler import SCHEMA_VERSION


def test_dimension_count():
    assert len(AESTHETIC_DIMENSIONS) == 11


def test_aesthetic_vector_to_array():
    v = AestheticVector.from_dict({"complexity": 0.4, "order": 0.8, "rhythm": 0.1})
    arr = v.to_array()
    assert len(arr) == 11
    assert abs(arr[0] - 0.4) < 1e-6
    assert abs(arr[1] - 0.8) < 1e-6
    assert abs(arr[10] - 0.1) < 1e-6


def test_dominant_dimensions():
    v = AestheticVector.from_dict({"order": 0.8, "balance": 0.7, "complexity": 0.1})
    dominant = v.dominant_dimensions()
    assert "order" in dominant
    assert "balance" in dominant
    assert "complexity" not in dominant


def test_dimension_score_clamp():
    ds = DimensionScore(value=1.5, confidence=1.2, direction="dominant")
    assert ds.value == 1.0
    assert ds.confidence == 1.0


def test_direction_helper():
    assert _direction(0.9) == "dominant"
    assert _direction(0.5) == "present"
    assert _direction(0.2) == "trace"
    assert _direction(0.05) == "absent"


def test_schema_version():
    ir = AestheticIR(
        document=Document(title="Test", source="test", sha256="abc"),
    )
    assert ir.schema_version == SCHEMA_VERSION


def test_defaults():
    ir = AestheticIR(document=Document(title="T", source="s", sha256="h"))
    assert ir.elements == []
    assert ir.projections == {}
    assert ir.cross_projection_disagreement is None

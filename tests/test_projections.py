import pytest
from aesthetics_compiler.ir.schemas import AestheticIR, Document, AestheticVector
from aesthetics_compiler.projections.birkhoff import BirkhoffProjection
from aesthetics_compiler.projections.arnheim import ArnheimProjection
from aesthetics_compiler.projections.berlyne import BerlyneProjection
from aesthetics_compiler.projections.gestalt import GestaltProjection


def _make_ir(scores: dict) -> AestheticIR:
    ir = AestheticIR(
        document=Document(title="Test", source="test", sha256="abc"),
        aggregate_aesthetic_vector=AestheticVector.from_dict(scores),
    )
    return ir


@pytest.mark.parametrize("proj_cls", [
    BirkhoffProjection, ArnheimProjection, BerlyneProjection, GestaltProjection
])
def test_projection_returns_result(proj_cls):
    ir = _make_ir({"order": 0.7, "complexity": 0.3, "balance": 0.7,
                   "contrast": 0.5, "saturation": 0.5, "tension": 0.3,
                   "closure": 0.2, "color_harmony": 0.8})
    result = proj_cls().run(ir)
    assert result.projection_id
    assert result.polarity in ("harmonious", "neutral", "discordant")
    assert -1.0 <= result.score <= 1.0


@pytest.mark.parametrize("proj_cls", [
    BirkhoffProjection, ArnheimProjection, BerlyneProjection, GestaltProjection
])
def test_projection_has_findings(proj_cls):
    ir = _make_ir({"order": 0.6, "complexity": 0.5, "balance": 0.6, "contrast": 0.5})
    result = proj_cls().run(ir)
    assert isinstance(result.findings, list)


def test_birkhoff_high_order_low_complexity_harmonious():
    ir = _make_ir({"order": 0.9, "complexity": 0.1})
    result = BirkhoffProjection().run(ir)
    assert result.polarity == "harmonious"


def test_berlyne_optimal_arousal():
    ir = _make_ir({"complexity": 0.5, "contrast": 0.5, "tension": 0.5, "saturation": 0.5, "closure": 0.3})
    result = BerlyneProjection().run(ir)
    assert result.polarity in ("harmonious", "neutral")

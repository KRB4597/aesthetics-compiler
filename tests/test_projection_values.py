"""Value-pinned projection tests.

Unlike test_projections.py (which only checks results are in range), these pin
the *actual numbers* the projection math produces for known inputs, and assert
the theory-driven *direction* of the relationships.

Two kinds of assertion are combined:

* ordering / direction  — robust, encodes the intended theory (e.g. Birkhoff
  rewards order and penalises complexity; Berlyne is an inverted-U in arousal).
* approximate value      — characterization: locks current behaviour so a silent
  formula/normalisation drift is caught.  If you change a formula on purpose,
  update the pinned number deliberately.
"""
import pytest

from aesthetics_compiler.ir.schemas import AestheticIR, AestheticVector, Document
from aesthetics_compiler.projections.arnheim import ArnheimProjection
from aesthetics_compiler.projections.berlyne import BerlyneProjection
from aesthetics_compiler.projections.birkhoff import BirkhoffProjection
from aesthetics_compiler.projections.gestalt import GestaltProjection

TOL = 0.03


def _ir(scores: dict) -> AestheticIR:
    return AestheticIR(
        document=Document(title="t", source="s", sha256="a"),
        aggregate_aesthetic_vector=AestheticVector.from_dict(scores),
    )


# ---------------------------------------------------------------- Birkhoff M=O/C
def test_birkhoff_monotonic_in_order_and_complexity():
    hi = BirkhoffProjection().run(_ir({"order": 0.9, "complexity": 0.1})).score
    mid = BirkhoffProjection().run(_ir({"order": 0.5, "complexity": 0.5})).score
    lo = BirkhoffProjection().run(_ir({"order": 0.1, "complexity": 0.9})).score
    # More order / less complexity must score strictly higher (Birkhoff M = O/C).
    assert hi > mid > lo


def test_birkhoff_pinned_values_and_polarity():
    hi = BirkhoffProjection().run(_ir({"order": 0.9, "complexity": 0.1}))
    lo = BirkhoffProjection().run(_ir({"order": 0.1, "complexity": 0.9}))
    assert hi.score == pytest.approx(0.842, abs=TOL)
    assert hi.polarity == "harmonious"
    assert lo.score == pytest.approx(0.072, abs=TOL)
    assert lo.polarity == "discordant"


# ------------------------------------------------------------ Berlyne inverted-U
def test_berlyne_inverted_u_peaks_at_mid_arousal():
    def arousal(a):
        return BerlyneProjection().run(
            _ir({"complexity": a, "contrast": a, "tension": a, "saturation": a, "closure": 0.3})
        ).score

    low, peak, high = arousal(0.1), arousal(0.5), arousal(0.9)
    # Hedonic value is highest at moderate arousal, lower at both extremes.
    assert peak > low
    assert peak > high
    assert peak == pytest.approx(0.998, abs=TOL)


# ----------------------------------------------------------- Arnheim / Gestalt
def test_arnheim_balanced_composition_harmonious():
    r = ArnheimProjection().run(
        _ir({"order": 0.7, "complexity": 0.3, "balance": 0.8,
             "contrast": 0.5, "tension": 0.3, "closure": 0.2})
    )
    assert r.score == pytest.approx(0.86, abs=TOL)
    assert r.polarity == "harmonious"


def test_gestalt_pinned_value():
    r = GestaltProjection().run(
        _ir({"order": 0.7, "complexity": 0.3, "closure": 0.2, "contrast": 0.6})
    )
    assert r.score == pytest.approx(0.624, abs=TOL)


def test_all_projection_scores_within_unit_range():
    # Sweep extremes; every projection must stay in [-1, 1] for any input.
    for s in ({d: 0.0 for d in AestheticVector().model_dump()},
              {"order": 1.0, "complexity": 1.0, "balance": 1.0, "contrast": 1.0,
               "tension": 1.0, "saturation": 1.0, "closure": 1.0, "color_harmony": 1.0}):
        ir = _ir(s)
        for proj in (BirkhoffProjection(), ArnheimProjection(),
                     BerlyneProjection(), GestaltProjection()):
            assert -1.0 <= proj.run(ir).score <= 1.0

"""Rule-extractor recall tests.

These iterate the actual vocabulary tables, so they are self-maintaining: if a
new artist/period entry is added that the matcher cannot recognise from a plain
sentence, the test fails — flagging a vocabulary entry that won't work.
"""
import pytest

from aesthetics_compiler.annotation.rule_extractor import (
    ARTIST_STYLE_MAP,
    RuleExtractor,
    STYLE_PERIOD_KEYWORDS,
)


def test_artist_recall_is_complete():
    ext = RuleExtractor()
    missed = [
        a for a in ARTIST_STYLE_MAP
        if ext.extract(f"A painting by {a}, oil on canvas.").artist_hint != a
    ]
    assert not missed, f"unrecognised artists: {missed}"


def test_style_period_recall_is_complete():
    ext = RuleExtractor()
    missed = [
        kw for kw, period in STYLE_PERIOD_KEYWORDS.items()
        if ext.extract(f"A work of {kw} art.").style_period_hint != period
    ]
    assert not missed, f"unrecognised style periods: {missed}"


MEDIUMS = ["oil", "acrylic", "watercolor", "charcoal", "ink",
           "digital", "photograph", "fresco", "tempera", "pastel", "pencil"]


@pytest.mark.parametrize("medium", MEDIUMS)
def test_medium_recall(medium):
    assert RuleExtractor().extract(f"A {medium} work on paper.").medium_hint is not None


def test_color_blocks_extracted():
    r = RuleExtractor().extract("Red and blue blocks on a white background.")
    names = " ".join(e.name for e in r.elements)
    assert "red" in names
    assert "blue" in names


def test_artist_style_priming_sets_dimensions():
    # A recognised artist should prime the aesthetic vector (Mondrian => high order).
    r = RuleExtractor().extract("A Mondrian composition.")
    assert r.elements
    orders = [e.aesthetic_vector.order.value for e in r.elements]
    assert max(orders) >= 0.7

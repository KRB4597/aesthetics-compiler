"""Tests for the extractor bake-off instrument.

These lock in the *findings* that motivate using spaCy over the rule extractor:
the rule extractor fails negation and substring traps; the spaCy contender
handles both.  (spaCy-dependent assertions skip cleanly if spaCy is absent.)
"""
import pytest

from benchmarks.contenders import RuleContender, SpacyContender


def test_rule_contender_scores_normal_text():
    s = RuleContender().score("A balanced, symmetrical composition.")
    assert s.get("balance", 0) >= 0.5
    assert s.get("order", 0) >= 0.5


def test_rule_contender_fails_negation_documented():
    # Documents the bug: the rule extractor reads "not balanced" as HIGH balance.
    s = RuleContender().score("A composition that is not balanced.")
    assert s.get("balance", 0) >= 0.5  # wrong, but this is current rule behaviour


def _spacy():
    c = SpacyContender()
    if not c.available():
        pytest.skip("spaCy / en_core_web_sm not installed")
    return c


def test_spacy_handles_negation():
    s = _spacy().score("A composition that is not balanced and not symmetrical.")
    assert s.get("balance", 1.0) < 0.5
    assert s.get("order", 1.0) < 0.5


def test_spacy_handles_substring_trap():
    # "unbalanced" must not trigger "balanced".
    s = _spacy().score("The layout is unbalanced.")
    assert s.get("balance", 1.0) < 0.5


def test_spacy_beats_rule_overall():
    from benchmarks.extractor_eval import GOLD, _judge
    rule, spacy = RuleContender(), _spacy()
    r_ok = r_tot = s_ok = s_tot = 0
    for text, _cat, high, low in GOLD:
        c, t = _judge(rule.score(text), high, low)
        r_ok += c; r_tot += t
        c, t = _judge(spacy.score(text), high, low)
        s_ok += c; s_tot += t
    assert (s_ok / s_tot) > (r_ok / r_tot)

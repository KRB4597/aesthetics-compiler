"""End-to-end tests for the spaCy 'nlp' extractor tier.

Skips cleanly if the [nlp] extra (spaCy + en_core_web_sm) isn't installed.
"""
import pytest

from aesthetics_compiler.pipeline.orchestrator import compile_document


def _require_spacy():
    try:
        from aesthetics_compiler.annotation.nlp_extractor import NlpExtractor
        NlpExtractor._load()
    except Exception:
        pytest.skip("spaCy / en_core_web_sm not installed ([nlp] extra)")


def test_nlp_tier_runs_and_tags_audit():
    _require_spacy()
    ir = compile_document("A balanced, symmetrical composition.",
                          extractor="nlp", quiet=True)
    assert "nlp" in ir.audit.extractor_tier.lower()
    assert ir.aggregate_aesthetic_vector.balance.value >= 0.5


def test_nlp_tier_handles_negation_where_rule_fails():
    _require_spacy()
    text = "A composition that is not balanced and not symmetrical."
    nlp_ir = compile_document(text, extractor="nlp", quiet=True)
    rule_ir = compile_document(text, extractor="rule", quiet=True)
    # The rule tier misreads negated adjectives as high; the nlp tier should not.
    assert nlp_ir.aggregate_aesthetic_vector.balance.value < \
        rule_ir.aggregate_aesthetic_vector.balance.value


def test_rule_tier_remains_default():
    ir = compile_document("A vibrant scene.", quiet=True)
    assert "rule" in ir.audit.extractor_tier.lower()

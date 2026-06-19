"""spaCy-backed text extractor (Tier: nlp).

A drop-in replacement for the rule extractor's dimension scoring that fixes the
keyword-bag failure modes measured by ``benchmarks/extractor_eval.py``:

  * word boundaries — "unbalanced" is its own token, so it never triggers
    "balanced" (the substring trap that diluted the rule extractor);
  * inflection      — matches on lemma too, so "ordering" registers order;
  * negation        — a syntactically negated keyword has its polarity inverted
    ("not balanced" reads LOW balance instead of high).

Everything else (elements, zones, colour schemes, motifs, facts, style/medium
detection) is inherited unchanged from RuleExtractor — only the dimension
scoring is replaced.

Requires the ``nlp`` extra: ``pip install -e ".[nlp]"`` plus the model,
``python -m spacy download en_core_web_sm``.
"""
from __future__ import annotations

from collections import defaultdict

from aesthetics_compiler.annotation import rule_extractor as _rx
from aesthetics_compiler.annotation.rule_extractor import RuleExtractor

_VOCABS: dict[str, dict[str, float]] = {
    "complexity": _rx.COMPLEXITY_KEYWORDS,
    "order": _rx.ORDER_KEYWORDS,
    "balance": _rx.BALANCE_KEYWORDS,
    "density": _rx.DENSITY_KEYWORDS,
    "hue_coherence": _rx.HUE_COHERENCE_KEYWORDS,
    "saturation": _rx.SATURATION_KEYWORDS,
    "contrast": _rx.CONTRAST_KEYWORDS,
    "color_harmony": _rx.COLOR_HARMONY_KEYWORDS,
    "tension": _rx.TENSION_KEYWORDS,
    "closure": _rx.CLOSURE_KEYWORDS,
    "rhythm": _rx.RHYTHM_KEYWORDS,
}

_NEG = {"not", "no", "never", "without", "lacking", "none", "non", "n't"}


class NlpExtractor(RuleExtractor):
    """Rule extractor with spaCy-based, negation-aware dimension scoring."""

    _nlp = None
    _lemma_index: dict[str, dict[str, float]] | None = None

    @classmethod
    def _load(cls):
        if cls._nlp is None:
            import spacy  # raises ImportError if the extra isn't installed
            cls._nlp = spacy.load("en_core_web_sm")
            index: dict[str, dict[str, float]] = {}
            for dim, vocab in _VOCABS.items():
                for kw, val in vocab.items():
                    if " " in kw:
                        continue
                    index.setdefault(cls._nlp(kw)[0].lemma_, {})[dim] = val
            cls._lemma_index = index
        return cls._nlp

    @staticmethod
    def _negated(tok) -> bool:
        for c in list(tok.children) + list(tok.head.children):
            if c.dep_ == "neg" or c.lower_ in _NEG:
                return True
        window = tok.doc[max(0, tok.i - 3):tok.i]
        return any(w.lower_ in _NEG for w in window)

    def _score_dimensions(self, lower: str) -> dict[str, float]:
        doc = self._load()(lower)
        hits: dict[str, list[float]] = defaultdict(list)
        for tok in doc:
            neg = self._negated(tok)
            matched: dict[str, float] = {}
            for dim, vocab in _VOCABS.items():
                if tok.lower_ in vocab:
                    matched[dim] = vocab[tok.lower_]
            for dim, val in self._lemma_index.get(tok.lemma_, {}).items():
                matched.setdefault(dim, val)
            for dim, val in matched.items():
                hits[dim].append(1.0 - val if neg else val)
        for dim, vocab in _VOCABS.items():
            for kw, val in vocab.items():
                if " " in kw and kw in doc.text:
                    idx = doc.text.find(kw)
                    head = next((t for t in doc if t.idx >= idx), None)
                    neg = self._negated(head) if head is not None else False
                    hits[dim].append(1.0 - val if neg else val)
        return {d: sum(v) / len(v) for d, v in hits.items() if v}

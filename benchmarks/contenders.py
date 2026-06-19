"""Extractor contenders for the bake-off.

Each contender turns a natural-language description into a dict of aesthetic
dimension scores in [0, 1].  They share the same vocabulary tables so the
comparison isolates the *matching strategy*, not the word lists:

  * RuleContender      — the current production extractor: lowercased substring
                         keyword matching, no negation, no word boundaries.
  * SpacyContender     — spaCy tokenisation: matches on token text AND lemma
                         (word boundaries + inflection), and inverts a keyword's
                         polarity when it is syntactically negated.
  * EmbeddingContender — sentence-transformers: scores each dimension by semantic
                         similarity of the text to positive/negative anchor
                         phrases (open-vocabulary; catches synonyms not in the
                         word lists).  Optional — skipped if the model can't load.

A contender is `available()` only if its dependencies import.
"""
from __future__ import annotations

from aesthetics_compiler.annotation.rule_extractor import RuleExtractor
from aesthetics_compiler.ir.schemas import AESTHETIC_DIMENSIONS

# The 11 dimension vocab tables, pulled straight from the rule extractor so all
# contenders compete on the same words.
from aesthetics_compiler.annotation import rule_extractor as _rx

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


class Contender:
    name = "base"

    def available(self) -> bool:
        return True

    def score(self, text: str) -> dict[str, float]:
        raise NotImplementedError


class RuleContender(Contender):
    name = "rule"

    def __init__(self) -> None:
        self._ext = RuleExtractor()

    def score(self, text: str) -> dict[str, float]:
        return self._ext._score_dimensions(text.lower())


class SpacyContender(Contender):
    """Wraps the real NlpExtractor so the bake-off tests the shipped code."""

    name = "spacy"

    def __init__(self) -> None:
        from aesthetics_compiler.annotation.nlp_extractor import NlpExtractor
        self._ext = NlpExtractor()

    def available(self) -> bool:
        try:
            self._ext._load()
            return True
        except Exception:
            return False

    def score(self, text: str) -> dict[str, float]:
        return self._ext._score_dimensions(text.lower())


class EmbeddingContender(Contender):
    name = "embedding"
    _model = None
    _anchors = None

    def available(self) -> bool:
        try:
            import sentence_transformers  # noqa: F401
            self._load()
            return True
        except Exception:
            return False

    @classmethod
    def _load(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            # Build positive/negative anchor centroids per dimension from the
            # high- and low-valued vocabulary words.
            import numpy as np
            anchors = {}
            for dim, vocab in _VOCABS.items():
                pos = [w for w, v in vocab.items() if v >= 0.6]
                neg = [w for w, v in vocab.items() if v <= 0.3]
                if not pos or not neg:
                    continue
                pe = cls._model.encode(pos, normalize_embeddings=True)
                ne = cls._model.encode(neg, normalize_embeddings=True)
                anchors[dim] = (np.asarray(pe).mean(0), np.asarray(ne).mean(0))
            cls._anchors = anchors
        return cls._model

    def score(self, text: str) -> dict[str, float]:
        import numpy as np
        model = self._load()
        emb = np.asarray(model.encode([text], normalize_embeddings=True))[0]
        out: dict[str, float] = {}
        for dim, (pos_c, neg_c) in self._anchors.items():
            diff = float(emb @ pos_c) - float(emb @ neg_c)
            out[dim] = 0.5 + 0.5 * np.tanh(4.0 * diff)  # map to [0,1]
        return out


def all_contenders() -> list[Contender]:
    return [RuleContender(), SpacyContender(), EmbeddingContender()]

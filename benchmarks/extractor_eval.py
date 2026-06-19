"""Extractor bake-off: which NLP strategy reads aesthetic descriptions best?

AADB (and AVA) are image datasets — they evaluate the *image* extractor, not the
text NLP tools.  To rank NLP tools we need labelled *text*.  This module holds a
small gold corpus of art descriptions, each annotated with which dimensions a
human would read as high or low, grouped by the linguistic phenomenon that
separates good extractors from bad ones:

  normal     — plain adjectives (baseline; everyone should get these)
  negation   — "not balanced" must read LOW, not high
  substring  — "unbalanced" must not trigger "balanced"
  inflection — "ordering" should still register order
  synonym    — out-of-vocabulary synonyms ("frenetic" ~ high tension)

Each contender scores every description; a dimension is predicted "high" if its
score >= 0.5.  We report accuracy overall and per category so you can see not
just who wins, but *where*.

Run:
    python -m benchmarks.extractor_eval
"""
from __future__ import annotations

from .contenders import all_contenders
from .metrics import strength  # noqa: F401  (kept for parity / future use)

THRESHOLD = 0.5

# (text, category, high-dimensions, low-dimensions)
GOLD: list[tuple[str, str, set[str], set[str]]] = [
    # --- normal -------------------------------------------------------------
    ("A balanced, symmetrical, ordered composition.", "normal", {"balance", "order"}, set()),
    ("A vibrant, vivid, saturated palette.", "normal", {"saturation"}, set()),
    ("A complex, intricate, busy scene.", "normal", {"complexity"}, set()),
    ("A calm, serene, peaceful, static mood.", "normal", set(), {"tension"}),
    ("A dense, packed layout.", "normal", {"density"}, set()),
    ("A monochromatic painting.", "normal", {"hue_coherence"}, set()),
    # --- negation -----------------------------------------------------------
    ("A composition that is not balanced and not symmetrical.", "negation", set(), {"balance", "order"}),
    ("The palette is not vibrant.", "negation", set(), {"saturation"}),
    ("This is not a complex image.", "negation", set(), {"complexity"}),
    ("The mood is not calm.", "negation", {"tension"}, set()),
    ("The colors are not harmonious.", "negation", set(), {"color_harmony"}),
    # --- substring traps ----------------------------------------------------
    ("The layout is unbalanced.", "substring", set(), {"balance"}),
    ("A nonsymmetrical, asymmetric arrangement.", "substring", set(), {"order"}),
    # --- inflection ---------------------------------------------------------
    ("The artist keeps ordering the elements.", "inflection", {"order"}, set()),
    # --- synonym / open-vocabulary (out-of-vocab words) ---------------------
    ("A frenetic, hectic, frenzied composition.", "synonym", {"tension"}, set()),
    ("An opulent, lavish, ornate design.", "synonym", {"complexity"}, set()),
    ("A tranquil, placid seascape.", "synonym", set(), {"tension"}),
]


def _judge(scores: dict[str, float], high: set[str], low: set[str]) -> tuple[int, int]:
    correct = total = 0
    for dim in high:
        total += 1
        correct += int(scores.get(dim, 0.0) >= THRESHOLD)
    for dim in low:
        total += 1
        correct += int(scores.get(dim, 0.0) < THRESHOLD)
    return correct, total


def run() -> int:
    contenders = [c for c in all_contenders() if c.available()]
    skipped = [c.name for c in all_contenders() if not c.available()]
    if skipped:
        print(f"(skipped unavailable contenders: {', '.join(skipped)})\n")

    categories = []
    for _, cat, _, _ in GOLD:
        if cat not in categories:
            categories.append(cat)

    # results[name][cat] = [correct, total]
    results: dict[str, dict[str, list[int]]] = {
        c.name: {cat: [0, 0] for cat in categories + ["ALL"]} for c in contenders
    }

    for text, cat, high, low in GOLD:
        for c in contenders:
            corr, tot = _judge(c.score(text), high, low)
            for bucket in (cat, "ALL"):
                results[c.name][bucket][0] += corr
                results[c.name][bucket][1] += tot

    names = [c.name for c in contenders]
    col_w = 11
    header = f"{'category':<12}" + "".join(f"{n:>{col_w}}" for n in names)
    print("Extractor bake-off - accuracy by linguistic phenomenon")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for cat in categories + ["ALL"]:
        row = f"{cat:<12}"
        for n in names:
            corr, tot = results[n][cat]
            row += f"{(corr / tot if tot else 0):>{col_w}.0%}"
        if cat == "ALL":
            print("-" * len(header))
        print(row)
    print("=" * len(header))

    overall = {n: results[n]["ALL"][0] / results[n]["ALL"][1] for n in names}
    winner = max(overall, key=overall.get)
    print(f"\nWinner overall: {winner} ({overall[winner]:.0%})")
    print("Read per-row to see where each tool wins (e.g. negation, synonym).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

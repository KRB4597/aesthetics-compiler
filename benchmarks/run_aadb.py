"""Evaluate the compiler against human aesthetic judgements (AADB).

What this does, in plain terms
------------------------------
For every labeled image it:
  1. runs the compiler  (``compile_document(image)``),
  2. reads back the predicted aesthetic dimensions and an overall score, and
  3. checks — across the whole set — whether the compiler's ranking of images
     agrees with the humans' ranking, using Spearman rank correlation.

It reports one correlation per mapped dimension (e.g. does the compiler's
``balance`` track AADB's ``balancing_element``?) plus one for the overall
score.  High positive numbers = the compiler captures that aspect of human
taste; near-zero = it doesn't; negative = it's backwards.

Usage
-----
    python -m benchmarks.run_aadb                      # bundled sample data
    python -m benchmarks.run_aadb --data labels.csv    # your real AADB CSV
    python -m benchmarks.run_aadb --data labels.csv --limit 500
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aesthetics_compiler.pipeline.orchestrator import compile_document

from .datasets import ATTRIBUTE_MAP, ensure_sample, load_labeled_images
from .metrics import spearman, strength


def _predicted_overall(ir) -> float:
    """Compiler proxy for 'overall aesthetic quality': mean projection score."""
    scores = [pr.score for pr in ir.projections.values()]
    return sum(scores) / len(scores) if scores else 0.0


def run(csv_path: Path, limit: int | None) -> int:
    samples = load_labeled_images(csv_path)
    if limit:
        samples = samples[:limit]
    if not samples:
        print("No samples found in", csv_path)
        return 1

    # Accumulators: paired (predicted, human) lists per mapped dimension + overall.
    pred: dict[str, list[float]] = {d: [] for d in ATTRIBUTE_MAP}
    human: dict[str, list[float]] = {d: [] for d in ATTRIBUTE_MAP}
    pred_overall: list[float] = []
    human_overall: list[float] = []

    ok, failed = 0, 0
    for s in samples:
        if not s.image.exists():
            print(f"  ! missing image, skipping: {s.image}", file=sys.stderr)
            failed += 1
            continue
        try:
            ir = compile_document(str(s.image), quiet=True)
        except Exception as exc:  # keep going; one bad image shouldn't abort
            print(f"  ! compile failed for {s.image.name}: {exc}", file=sys.stderr)
            failed += 1
            continue
        ok += 1

        vec = ir.aggregate_aesthetic_vector
        for dim, attr_col in ATTRIBUTE_MAP.items():
            if attr_col in s.attributes:
                pred[dim].append(getattr(vec, dim).value)
                human[dim].append(s.attributes[attr_col])

        if s.overall is not None:
            pred_overall.append(_predicted_overall(ir))
            human_overall.append(s.overall)

    print()
    print(f"Compiled {ok} images ({failed} skipped) from {csv_path.name}")
    print("=" * 64)
    print(f"{'compiler dimension':<20}{'vs AADB attribute':<22}{'n':>4}  {'Spearman':>9}  strength")
    print("-" * 64)
    for dim, attr_col in ATTRIBUTE_MAP.items():
        n = len(pred[dim])
        r = spearman(pred[dim], human[dim]) if n >= 2 else float("nan")
        rtxt = f"{r:+.3f}" if r == r else "   n/a"
        print(f"{dim:<20}{attr_col:<22}{n:>4}  {rtxt:>9}  {strength(r)}")
    print("-" * 64)
    n = len(pred_overall)
    r = spearman(pred_overall, human_overall) if n >= 2 else float("nan")
    rtxt = f"{r:+.3f}" if r == r else "   n/a"
    print(f"{'overall (mean proj)':<20}{'overall':<22}{n:>4}  {rtxt:>9}  {strength(r)}")
    print("=" * 64)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Evaluate aesthetics-compiler against AADB human labels.")
    p.add_argument("--data", type=Path, default=None,
                   help="CSV of AADB labels (see benchmarks/README.md). Omit to use bundled sample.")
    p.add_argument("--limit", type=int, default=None, help="Only evaluate the first N images.")
    args = p.parse_args(argv)

    if args.data is None:
        csv_path = ensure_sample()
        print("NOTE: using the bundled SAMPLE dataset (6 synthetic images).")
        print("      Numbers below are a smoke test, not a real evaluation.")
        print("      Pass --data <aadb.csv> with real labels for meaningful results.")
    else:
        csv_path = args.data
        if not csv_path.exists():
            print(f"Data file not found: {csv_path}", file=sys.stderr)
            return 1

    return run(csv_path, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())

"""Regression tests for bugs that previously shipped green.

Each test here corresponds to a real defect that the original suite did not
catch.  They are written to FAIL on the old (buggy) code and PASS on the fix.
"""
import subprocess
import sys

from aesthetics_compiler.ir.graph.schema import EdgeKind
from aesthetics_compiler.pipeline.orchestrator import compile_document

# Text engineered to yield a motif (grid/repeating) and a dominant_tension fact,
# which are the sources for GROUPED_WITH and GENERATES_TENSION edges.
_RICH = ("A tense, explosive, chaotic composition of repeating red and blue "
         "blocks in a grid pattern, dynamic and restless, with strident "
         "energetic strokes.")


def test_promote_emits_grouped_with_edges():
    """promote.py must synthesise GROUPED_WITH from shared motifs.

    Bug: no relational edges were created, so GestaltProjection's grouping
    bonus was permanently zero.
    """
    ir = compile_document(_RICH, quiet=True)
    grouped = [e for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.GROUPED_WITH]
    assert len(grouped) > 0, "expected GROUPED_WITH edges from the grid motif"


def test_promote_emits_generates_tension_edges():
    """promote.py must synthesise GENERATES_TENSION from dominant_tension facts.

    Bug: TensionModule's edge bonus was permanently zero.
    """
    ir = compile_document(_RICH, quiet=True)
    gen = [e for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.GENERATES_TENSION]
    assert len(gen) > 0, "expected GENERATES_TENSION edges from the tension fact"


def test_tension_explanation_counts_only_tension_edges():
    """The tension explanation reports the GENERATES_TENSION count, not all edges.

    Bug: it printed len(all edges) mislabeled as 'tension edges'.
    """
    ir = compile_document(_RICH, quiet=True)
    gen = sum(1 for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.GENERATES_TENSION)
    expl = ir.aggregate_aesthetic_vector.tension.explanation
    assert f"tension edges {gen}" in expl


def test_cli_runs_as_module():
    """`python -m aesthetics_compiler.cli` must actually run.

    Bug: the module had no `if __name__ == '__main__': app()` guard, so it
    imported and exited 0 doing nothing.
    """
    out = subprocess.run(
        [sys.executable, "-m", "aesthetics_compiler.cli", "version"],
        capture_output=True, text=True,
    )
    assert out.returncode == 0
    assert "aesthetics-compiler" in out.stdout


def test_no_llm_tier_advertised():
    """The unimplemented LLM tier was removed from CompilerTier."""
    from aesthetics_compiler.tiers import CompilerTier
    assert "llm" not in {t.value for t in CompilerTier}


def test_degenerate_input_does_not_crash():
    """A trivial input still produces a valid IR (fallback element, no exception)."""
    ir = compile_document("a", quiet=True)
    assert len(ir.elements) >= 1
    assert ir.audit.graph_hash and len(ir.audit.graph_hash) == 64
    for pr in ir.projections.values():
        assert -1.0 <= pr.score <= 1.0

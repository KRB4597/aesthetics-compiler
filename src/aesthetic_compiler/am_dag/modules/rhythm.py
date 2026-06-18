"""RhythmModule (k=10) — temporal pacing. 0 for static; computed for multimedia."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.rhythm.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # motif repetition also contributes to visual rhythm even in static work
    repetition_motifs = [m for m in ir.motifs if m.motif_type in ("repetition", "rhythm", "pattern")]
    motif_boost = min(0.2, len(repetition_motifs) * 0.07)

    # for static images this stays near 0; for animated content base is already set
    adjusted = min(1.0, base + motif_boost)

    ctx["rhythm"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.65,
        direction=_direction(adjusted),
        explanation=f"Rhythm {adjusted:.2f}; {len(repetition_motifs)} repetition motif(s)",
    )

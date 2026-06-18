"""HueCoherenceModule (k=4) — root (no upstream spatial deps)."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.hue_coherence.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # monochromatic color scheme boosts coherence
    for cs in ir.color_schemes:
        if cs.harmony_type == "monochromatic":
            base = min(1.0, base + 0.1)
        elif cs.harmony_type == "polychromatic":
            base = max(0.0, base - 0.05)

    ctx["hue_coherence"] = base
    return DimensionScore(
        value=base,
        confidence=0.75,
        direction=_direction(base),
        explanation=f"Hue coherence {base:.2f}; {len(ir.color_schemes)} color scheme(s) detected",
    )

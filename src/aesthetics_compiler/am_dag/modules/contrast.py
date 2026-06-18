"""ContrastModule (k=6) — reads balance, density ctx."""
from aesthetics_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.contrast.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # aesthetic facts about high contrast adjust the score
    high_contrast_facts = [
        f for f in ir.aesthetic_facts if f.dimension == "contrast" and f.severity in ("high", "moderate")
    ]
    if high_contrast_facts:
        base = min(1.0, base + 0.05)

    ctx["contrast"] = base
    return DimensionScore(
        value=base,
        confidence=0.75,
        direction=_direction(base),
        explanation=f"Contrast {base:.2f}; {len(high_contrast_facts)} contrast fact(s)",
    )

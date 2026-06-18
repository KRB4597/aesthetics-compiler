"""SaturationModule (k=5) — reads hue_coherence ctx."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.saturation.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # low hue coherence with high saturation → garish risk
    hue_coherence = ctx.get("hue_coherence", 0.5)
    if base > 0.7 and hue_coherence < 0.3:
        # many saturated hues = polychromatic clash
        base = base  # keep score but note the fact
        from aesthetic_compiler.ir.schemas import AestheticFact
        ir.aesthetic_facts.append(AestheticFact(
            id="fact:saturation_clash",
            fact_kind="color_clash",
            dimension="saturation",
            severity="moderate",
            confidence=0.7,
            explanation="High saturation with low hue coherence risks visual clash",
        ))

    ctx["saturation"] = base
    return DimensionScore(
        value=base,
        confidence=0.75,
        direction=_direction(base),
        explanation=f"Saturation {base:.2f}; hue coherence context {hue_coherence:.2f}",
    )

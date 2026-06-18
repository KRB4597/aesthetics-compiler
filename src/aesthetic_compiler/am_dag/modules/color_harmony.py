"""ColorHarmonyModule (k=7) — reads hue_coherence, saturation ctx."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction

_HARMONY_SCORE_MAP = {
    "monochromatic": 0.9,
    "analogous": 0.85,
    "complementary": 0.85,
    "split_complementary": 0.80,
    "triadic": 0.80,
    "tetradic": 0.70,
    "polychromatic": 0.45,
    "achromatic": 0.80,
}


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.color_harmony.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # color scheme harmony type provides strong signal
    scheme_bonus = 0.0
    for cs in ir.color_schemes:
        scheme_score = _HARMONY_SCORE_MAP.get(cs.harmony_type, 0.5)
        scheme_bonus = max(scheme_bonus, scheme_score - 0.5)  # positive lift only

    # saturation coherence: harmonious saturation boosts harmony
    saturation = ctx.get("saturation", 0.5)
    hue_coherence = ctx.get("hue_coherence", 0.5)
    coherence_boost = 0.05 * (hue_coherence - 0.5)

    adjusted = max(0.0, min(1.0, base + scheme_bonus * 0.3 + coherence_boost))

    ctx["color_harmony"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.75,
        direction=_direction(adjusted),
        explanation=f"Color harmony {adjusted:.2f}; scheme bonus {scheme_bonus:.2f}; coherence boost {coherence_boost:.2f}",
    )

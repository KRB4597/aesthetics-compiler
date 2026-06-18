"""DensityModule (k=3) — reads complexity ctx."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.density.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # negative-space zones pull density down
    neg_space = sum(1 for z in ir.zones if z.zone_type in ("periphery",) and z.salience < 0.3)
    neg_penalty = min(0.15, neg_space * 0.05)

    complexity = ctx.get("complexity", 0.5)
    # complexity drives density upward
    adjusted = min(1.0, base + 0.1 * complexity - neg_penalty)
    adjusted = max(0.0, adjusted)

    ctx["density"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.7,
        direction=_direction(adjusted),
        explanation=f"Density {adjusted:.2f} (complexity contribution {0.1 * complexity:.2f})",
    )

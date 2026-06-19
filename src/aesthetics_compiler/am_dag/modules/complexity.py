"""ComplexityModule (k=0) — root, no upstream deps."""
from aesthetics_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.complexity.value for e in ir.elements if e.aesthetic_vector]
    base = sum(vals) / max(1, len(vals))

    # penalise large element counts as a proxy for clutter
    element_count = len(ir.elements)
    if element_count > 15:
        base = min(1.0, base + 0.05 * (element_count - 15) / 10)

    ctx["complexity"] = base
    return DimensionScore(
        value=base,
        confidence=0.75,
        direction=_direction(base),
        explanation=f"Mean element complexity {base:.2f} across {element_count} elements",
    )

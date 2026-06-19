"""ClosureModule (k=9) — reads complexity, order ctx. Gestalt completion demand."""
from aesthetics_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.closure.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # closure_gap facts raise the demand score
    gap_facts = [f for f in ir.aesthetic_facts if f.fact_kind == "closure_gap"]
    gap_boost = min(0.2, len(gap_facts) * 0.07)

    # figure_ground ambiguity facts
    ambiguity_facts = [f for f in ir.aesthetic_facts if f.fact_kind == "figure_ground_ambiguity"]
    ambiguity_boost = min(0.15, len(ambiguity_facts) * 0.05)

    # high complexity with low order → more open/unresolved forms
    complexity = ctx.get("complexity", 0.5)
    order = ctx.get("order", 0.5)
    implicit_closure = 0.1 * max(0, complexity - order)

    adjusted = min(1.0, base + gap_boost + ambiguity_boost + implicit_closure)
    adjusted = max(0.0, adjusted)

    ctx["closure"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.7,
        direction=_direction(adjusted),
        explanation=f"Closure demand {adjusted:.2f}; implicit {implicit_closure:.2f} from complexity-order gap",
    )

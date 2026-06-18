"""OrderModule (k=1) — reads complexity ctx."""
from aesthetics_compiler.ir.schemas import AestheticIR, DimensionScore, _direction
from aesthetics_compiler.ir.graph.schema import EdgeKind


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.order.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    symmetry_bonus = 0.0
    if ir.aesthetic_graph:
        mirror_edges = [e for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.MIRRORS]
        symmetry_bonus = min(0.15, len(mirror_edges) * 0.05)

    # high complexity slightly penalises perceived order
    complexity = ctx.get("complexity", 0.5)
    adjusted = base + symmetry_bonus - 0.1 * max(0, complexity - 0.6)
    adjusted = max(0.0, min(1.0, adjusted))

    ctx["order"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.75,
        direction=_direction(adjusted),
        explanation=f"Order {adjusted:.2f}; symmetry bonus {symmetry_bonus:.2f}; complexity penalty from {complexity:.2f}",
    )

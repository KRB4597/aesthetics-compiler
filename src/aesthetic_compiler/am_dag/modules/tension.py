"""TensionModule (k=8) — reads order, balance ctx. Arnheim visual dynamics."""
from aesthetic_compiler.ir.schemas import AestheticIR, DimensionScore, _direction
from aesthetic_compiler.ir.graph.schema import EdgeKind


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.tension.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # GENERATES_TENSION edges amplify tension
    tension_boost = 0.0
    if ir.aesthetic_graph:
        gen_edges = [e for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.GENERATES_TENSION]
        tension_boost = min(0.2, len(gen_edges) * 0.05)

    # low balance → higher tension (Arnheim: off-balance compositions feel tense)
    balance = ctx.get("balance", 0.5)
    balance_contribution = 0.15 * max(0, 0.5 - balance)

    # low order → chaos rather than tension; moderate order → tension
    order = ctx.get("order", 0.5)
    order_contribution = 0.0
    if 0.2 < order < 0.6:
        order_contribution = 0.05

    adjusted = min(1.0, base + tension_boost + balance_contribution + order_contribution)
    adjusted = max(0.0, adjusted)

    ctx["tension"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.7,
        direction=_direction(adjusted),
        explanation=f"Tension {adjusted:.2f}; balance contribution {balance_contribution:.2f}; tension edges {len(ir.aesthetic_graph.edges) if ir.aesthetic_graph else 0}",
    )

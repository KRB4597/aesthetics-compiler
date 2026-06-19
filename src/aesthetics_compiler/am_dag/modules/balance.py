"""BalanceModule (k=2) — reads order ctx."""
from aesthetics_compiler.ir.schemas import AestheticIR, DimensionScore, _direction


def evaluate(ir: AestheticIR, ctx: dict) -> DimensionScore:
    vals = [e.aesthetic_vector.balance.value for e in ir.elements]
    base = sum(vals) / max(1, len(vals))

    # zone salience modulates balance: high-salience periphery zones indicate imbalance
    salience_penalty = 0.0
    for zone in ir.zones:
        if zone.zone_type == "periphery" and zone.salience > 0.7:
            salience_penalty += 0.1

    order = ctx.get("order", 0.5)
    # high order tends to correlate with better balance (grid/symmetry = balanced)
    order_boost = 0.05 * max(0, order - 0.5)

    adjusted = max(0.0, min(1.0, base + order_boost - salience_penalty))

    ctx["balance"] = adjusted
    return DimensionScore(
        value=adjusted,
        confidence=0.7,
        direction=_direction(adjusted),
        explanation=f"Balance {adjusted:.2f}; order boost {order_boost:.2f}; salience penalty {salience_penalty:.2f}",
    )

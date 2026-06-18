from __future__ import annotations
from aesthetics_compiler.ir.schemas import AestheticIR, AestheticVector, DimensionScore, _direction
from aesthetics_compiler.am_dag.modules import (
    complexity, order, balance, density,
    hue_coherence, saturation, contrast, color_harmony,
    tension, closure, rhythm,
)

_MODULE_ORDER = [
    ("complexity",    complexity.evaluate),
    ("order",         order.evaluate),
    ("hue_coherence", hue_coherence.evaluate),
    ("balance",       balance.evaluate),
    ("density",       density.evaluate),
    ("saturation",    saturation.evaluate),
    ("contrast",      contrast.evaluate),
    ("color_harmony", color_harmony.evaluate),
    ("tension",       tension.evaluate),
    ("closure",       closure.evaluate),
    ("rhythm",        rhythm.evaluate),
]


class AMDAG:
    def evaluate(self, ir: AestheticIR) -> AestheticVector:
        ctx: dict = {}
        results: dict[str, DimensionScore] = {}
        for dim_name, fn in _MODULE_ORDER:
            results[dim_name] = fn(ir, ctx)
        return AestheticVector(**results)

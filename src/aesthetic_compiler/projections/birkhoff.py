"""BirkhoffProjection — M = log(1+O)/(1+C) aesthetic measure."""
import math
from aesthetic_compiler.ir.schemas import AestheticIR, ProjectionResult, AestheticFinding
from aesthetic_compiler.projections.base import BaseProjection


class BirkhoffProjection(BaseProjection):
    projection_id = "birkhoff"

    def run(self, ir: AestheticIR) -> ProjectionResult:
        vec = ir.aggregate_aesthetic_vector
        order = vec.order.value
        complexity = vec.complexity.value

        M = math.log(1.0 + order) / (1.0 + complexity)
        M_norm = min(1.0, M / math.log(2))

        findings: list[AestheticFinding] = []

        order_deficit = max(0.0, 0.7 - order)
        if order_deficit > 0.1:
            findings.append(AestheticFinding(
                finding_type="order_deficit",
                score=-order_deficit,
                explanation=f"Order {order:.2f} is below the 0.7 harmonious threshold; composition could gain from additional structure",
            ))
        else:
            findings.append(AestheticFinding(
                finding_type="sufficient_order",
                score=order,
                explanation=f"Order {order:.2f} is sufficient for positive Birkhoff measure",
            ))

        complexity_excess = max(0.0, complexity - 0.6)
        if complexity_excess > 0.1:
            findings.append(AestheticFinding(
                finding_type="complexity_excess",
                score=-complexity_excess,
                explanation=f"Complexity {complexity:.2f} depresses the M ratio; simplification may improve measure",
            ))

        findings.append(AestheticFinding(
            finding_type="birkhoff_measure",
            score=M_norm,
            explanation=f"M = log(1+{order:.2f})/(1+{complexity:.2f}) = {M:.3f} (normalised {M_norm:.2f})",
        ))

        if M_norm >= 0.65:
            verdict, polarity = "high_aesthetic_measure", "harmonious"
        elif M_norm >= 0.40:
            verdict, polarity = "moderate_aesthetic_measure", "neutral"
        elif M_norm >= 0.20:
            verdict, polarity = "low_aesthetic_measure", "neutral"
        else:
            verdict, polarity = "complexity_dominated", "discordant"

        return ProjectionResult(
            projection_id=self.projection_id,
            verdict=verdict,
            polarity=polarity,
            findings=findings,
            score=M_norm,
            explanation=f"Birkhoff M={M:.3f}; order={order:.2f}; complexity={complexity:.2f}",
        )

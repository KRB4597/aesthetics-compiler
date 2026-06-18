"""BerlyneProjection — arousal potential and inverted-U hedonic curve."""
import math
from aesthetic_compiler.ir.schemas import AestheticIR, ProjectionResult, AestheticFinding
from aesthetic_compiler.projections.base import BaseProjection

_OPTIMAL_AROUSAL = 0.50
_AROUSAL_WEIGHTS = {
    "complexity": 0.30,
    "contrast":   0.25,
    "tension":    0.20,
    "saturation": 0.15,
    "closure":    0.10,
}


class BerlyneProjection(BaseProjection):
    projection_id = "berlyne"

    def run(self, ir: AestheticIR) -> ProjectionResult:
        vec = ir.aggregate_aesthetic_vector

        arousal = sum(
            getattr(vec, dim).value * weight
            for dim, weight in _AROUSAL_WEIGHTS.items()
        )

        hedonic = 1.0 - (abs(arousal - _OPTIMAL_AROUSAL) / _OPTIMAL_AROUSAL) ** 2
        hedonic = max(-1.0, min(1.0, hedonic))

        findings: list[AestheticFinding] = []

        findings.append(AestheticFinding(
            finding_type="arousal_potential",
            score=arousal,
            explanation=f"Berlyne arousal potential A={arousal:.2f} (optimal={_OPTIMAL_AROUSAL})",
        ))
        findings.append(AestheticFinding(
            finding_type="predicted_hedonic_value",
            score=hedonic,
            explanation=f"Hedonic value H={hedonic:.2f} on inverted-U curve; deviation from optimal={abs(arousal - _OPTIMAL_AROUSAL):.2f}",
        ))

        for dim, weight in _AROUSAL_WEIGHTS.items():
            val = getattr(vec, dim).value
            contribution = val * weight
            if contribution > 0.1:
                findings.append(AestheticFinding(
                    finding_type=f"arousal_contribution:{dim}",
                    score=contribution,
                    explanation=f"{dim}={val:.2f} contributes {contribution:.2f} to arousal (weight {weight})",
                ))

        if arousal > 0.75:
            findings.append(AestheticFinding(
                finding_type="overarousal",
                score=-(arousal - 0.75),
                explanation="Berlyne overarousal: composition may be perceived as overwhelming or aversive",
            ))
        elif arousal < 0.20:
            findings.append(AestheticFinding(
                finding_type="underarousal",
                score=-(0.20 - arousal),
                explanation="Berlyne underarousal: composition may be perceived as boring or inert",
            ))

        if hedonic >= 0.65:
            verdict, polarity = "optimal_arousal", "harmonious"
        elif hedonic >= 0.30:
            verdict, polarity = "moderate_arousal", "neutral"
        elif arousal > _OPTIMAL_AROUSAL:
            verdict, polarity = "overarousal_aversive", "discordant"
        else:
            verdict, polarity = "underarousal_boring", "discordant"

        return ProjectionResult(
            projection_id=self.projection_id,
            verdict=verdict,
            polarity=polarity,
            findings=findings,
            score=round(hedonic, 3),
            explanation=f"Berlyne A={arousal:.2f}, H={hedonic:.2f}; verdict={verdict}",
        )

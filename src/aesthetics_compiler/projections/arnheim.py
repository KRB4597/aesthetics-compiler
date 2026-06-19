"""ArnheimProjection — visual dynamics: balance, tension, spatial equilibrium."""
from aesthetics_compiler.ir.schemas import AestheticIR, ProjectionResult, AestheticFinding
from aesthetics_compiler.projections.base import BaseProjection


class ArnheimProjection(BaseProjection):
    projection_id = "arnheim"

    def run(self, ir: AestheticIR) -> ProjectionResult:
        vec = ir.aggregate_aesthetic_vector
        balance = vec.balance.value
        tension = vec.tension.value
        order = vec.order.value

        findings: list[AestheticFinding] = []

        # Balance analysis
        if balance >= 0.7:
            findings.append(AestheticFinding(
                finding_type="spatial_equilibrium",
                score=balance,
                explanation=f"Arnheim equilibrium achieved: visual weight centered (balance={balance:.2f})",
            ))
        elif balance >= 0.4:
            findings.append(AestheticFinding(
                finding_type="dynamic_balance",
                score=balance,
                explanation=f"Asymmetric balance: composition has Arnheim 'active equilibrium' (balance={balance:.2f})",
            ))
        else:
            findings.append(AestheticFinding(
                finding_type="visual_imbalance",
                score=-balance,
                explanation=f"Visual weight strongly off-center (balance={balance:.2f}); Arnheim identifies tension without resolution",
            ))

        # Tension analysis
        if tension >= 0.65:
            findings.append(AestheticFinding(
                finding_type="high_visual_tension",
                score=tension,
                explanation=f"Dominant directional forces detected (tension={tension:.2f}); Arnheim's centrifugal composition",
            ))
        elif tension >= 0.35:
            findings.append(AestheticFinding(
                finding_type="moderate_tension",
                score=tension,
                explanation=f"Moderate visual tension contributes to dynamism (tension={tension:.2f})",
            ))
        else:
            findings.append(AestheticFinding(
                finding_type="static_composition",
                score=0.0,
                explanation=f"Low tension; composition is static and restful (tension={tension:.2f})",
            ))

        # Balance-tension relationship (Arnheim's key insight)
        bt_score = balance * (1.0 - 0.3 * tension)
        if balance >= 0.6 and tension >= 0.4:
            findings.append(AestheticFinding(
                finding_type="arnheim_ideal",
                score=bt_score,
                explanation="Arnheim ideal: balanced composition with expressive tension",
            ))

        aggregate_score = balance * 0.6 + (1.0 - abs(tension - 0.35)) * 0.4

        if aggregate_score >= 0.65:
            verdict, polarity = "spatial_equilibrium", "harmonious"
        elif aggregate_score >= 0.45:
            verdict, polarity = "dynamic_tension", "harmonious"
        elif aggregate_score >= 0.25:
            verdict, polarity = "moderate_imbalance", "neutral"
        else:
            verdict, polarity = "structural_discord", "discordant"

        return ProjectionResult(
            projection_id=self.projection_id,
            verdict=verdict,
            polarity=polarity,
            findings=findings,
            score=round(aggregate_score, 3),
            explanation=f"Arnheim: balance={balance:.2f}, tension={tension:.2f}; aggregate={aggregate_score:.2f}",
        )

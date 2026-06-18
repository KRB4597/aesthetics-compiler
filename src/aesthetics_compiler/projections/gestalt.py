"""GestaltProjection — grouping coherence, figure-ground, closure."""
from aesthetics_compiler.ir.schemas import AestheticIR, ProjectionResult, AestheticFinding
from aesthetics_compiler.projections.base import BaseProjection
from aesthetics_compiler.ir.graph.schema import EdgeKind


class GestaltProjection(BaseProjection):
    projection_id = "gestalt"

    def run(self, ir: AestheticIR) -> ProjectionResult:
        vec = ir.aggregate_aesthetic_vector
        closure = vec.closure.value
        order = vec.order.value
        contrast = vec.contrast.value

        findings: list[AestheticFinding] = []

        # Grouping strength from GROUPED_WITH edges
        grouping_strength = 0.5
        if ir.aesthetic_graph:
            grouped = [e for e in ir.aesthetic_graph.edges if e.kind == EdgeKind.GROUPED_WITH]
            total_elems = max(1, len(ir.aesthetic_graph.element_nodes()))
            grouping_strength = min(1.0, len(grouped) / total_elems + 0.3)
        findings.append(AestheticFinding(
            finding_type="grouping_strength",
            score=grouping_strength,
            explanation=f"Gestalt grouping coherence: {grouping_strength:.2f}",
        ))

        # Figure-ground clarity from contrast
        fg_clarity = contrast
        findings.append(AestheticFinding(
            finding_type="figure_ground_clarity",
            score=fg_clarity,
            explanation=f"Figure-ground clarity derived from contrast={contrast:.2f}",
        ))

        # Closure satisfaction (inverted: high closure demand = lower satisfaction)
        closure_satisfaction = max(0.0, 1.0 - closure * 0.7)
        findings.append(AestheticFinding(
            finding_type="closure_satisfaction",
            score=closure_satisfaction,
            explanation=f"Closure satisfaction {closure_satisfaction:.2f}; demand was {closure:.2f}",
        ))

        # Wholeness / unity: order × grouping × closure_satisfaction
        unity = (order * 0.4 + grouping_strength * 0.3 + closure_satisfaction * 0.3)
        findings.append(AestheticFinding(
            finding_type="unity_index",
            score=unity,
            explanation=f"Gestalt unity {unity:.2f} = order({order:.2f})×0.4 + grouping({grouping_strength:.2f})×0.3 + closure_sat({closure_satisfaction:.2f})×0.3",
        ))

        # Facts about figure-ground ambiguity
        fg_facts = [f for f in ir.aesthetic_facts if f.fact_kind == "figure_ground_ambiguity"]
        if fg_facts:
            findings.append(AestheticFinding(
                finding_type="figure_ground_ambiguity_detected",
                score=-0.2,
                explanation=f"{len(fg_facts)} figure-ground ambiguity fact(s) reduce Gestalt clarity",
            ))

        aggregate_score = unity * 0.5 + fg_clarity * 0.3 + grouping_strength * 0.2

        if aggregate_score >= 0.65:
            verdict, polarity = "gestalt_coherent", "harmonious"
        elif aggregate_score >= 0.45:
            verdict, polarity = "partial_gestalt_unity", "neutral"
        elif aggregate_score >= 0.25:
            verdict, polarity = "fragmented_composition", "neutral"
        else:
            verdict, polarity = "gestalt_dissolution", "discordant"

        return ProjectionResult(
            projection_id=self.projection_id,
            verdict=verdict,
            polarity=polarity,
            findings=findings,
            score=round(aggregate_score, 3),
            explanation=f"Gestalt unity={unity:.2f}; fg_clarity={fg_clarity:.2f}; grouping={grouping_strength:.2f}",
        )

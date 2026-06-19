from aesthetics_compiler.ir.schemas import AestheticIR, AESTHETIC_DIMENSIONS
from aesthetics_compiler.ir.graph.container import AestheticGraph
from aesthetics_compiler.ir.graph.schema import AestheticNode, AestheticEdge, NodeKind, EdgeKind


def graph_from_ir(ir: AestheticIR) -> AestheticGraph:
    g = AestheticGraph()

    for elem in ir.elements:
        scores = {d: getattr(elem.aesthetic_vector, d).value for d in AESTHETIC_DIMENSIONS}
        g.add_node(AestheticNode(
            id=elem.id,
            kind=NodeKind.ELEMENT,
            label=elem.name,
            aesthetic_scores=scores,
            metadata={"element_type": elem.element_type, "size_ratio": elem.size_ratio},
        ))

    for zone in ir.zones:
        g.add_node(AestheticNode(
            id=zone.id,
            kind=NodeKind.ZONE,
            label=zone.zone_type,
            metadata={"salience": zone.salience},
        ))
        for eid in zone.element_ids:
            if eid in g.nodes:
                g.add_edge(AestheticEdge(src=zone.id, dst=eid, kind=EdgeKind.CONTAINS))

    for cs in ir.color_schemes:
        g.add_node(AestheticNode(
            id=cs.id,
            kind=NodeKind.COLOR_SCHEME,
            label=cs.harmony_type,
            aesthetic_scores={"saturation": cs.saturation_avg},
            metadata={"dominant_hue_deg": cs.dominant_hue_deg, "lightness_avg": cs.lightness_avg},
        ))
        for eid in cs.element_ids:
            if eid in g.nodes:
                g.add_edge(AestheticEdge(src=eid, dst=cs.id, kind=EdgeKind.BELONGS_TO))

    for motif in ir.motifs:
        g.add_node(AestheticNode(
            id=motif.id,
            kind=NodeKind.MOTIF,
            label=motif.motif_type,
            metadata={"frequency": motif.frequency},
        ))
        present = [eid for eid in motif.element_ids if eid in g.nodes]
        for eid in present:
            g.add_edge(AestheticEdge(src=eid, dst=motif.id, kind=EdgeKind.PART_OF_MOTIF))
        # Elements sharing a motif are perceptually grouped (Gestalt similarity/
        # proximity).  Emit GROUPED_WITH edges so GestaltProjection's grouping
        # bonus is actually fed; without these it is permanently zero.
        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                g.add_edge(AestheticEdge(
                    src=present[i], dst=present[j], kind=EdgeKind.GROUPED_WITH,
                ))

    for fact in ir.aesthetic_facts:
        g.add_node(AestheticNode(
            id=fact.id,
            kind=NodeKind.FACT,
            label=fact.fact_kind,
            metadata={"severity": fact.severity, "dimension": fact.dimension},
        ))
        # A dominant-tension fact names the elements generating directional
        # tension.  Materialise it as a tension_vector node with GENERATES_TENSION
        # edges so TensionModule's edge bonus is fed (otherwise always zero).
        if fact.fact_kind == "dominant_tension":
            tv_id = f"tension_vec:{fact.id}"
            g.add_node(AestheticNode(
                id=tv_id,
                kind=NodeKind.TENSION_VEC,
                label="dominant_tension",
                metadata={"severity": fact.severity},
            ))
            for eid in fact.subject_ids:
                if eid in g.nodes:
                    g.add_edge(AestheticEdge(
                        src=eid, dst=tv_id, kind=EdgeKind.GENERATES_TENSION,
                    ))

    return g

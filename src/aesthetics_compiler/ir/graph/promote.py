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
        for eid in motif.element_ids:
            if eid in g.nodes:
                g.add_edge(AestheticEdge(src=eid, dst=motif.id, kind=EdgeKind.PART_OF_MOTIF))

    for fact in ir.aesthetic_facts:
        g.add_node(AestheticNode(
            id=fact.id,
            kind=NodeKind.FACT,
            label=fact.fact_kind,
            metadata={"severity": fact.severity, "dimension": fact.dimension},
        ))

    return g

from aesthetics_compiler.ir.graph.schema import AestheticNode, AestheticEdge, NodeKind, EdgeKind
from aesthetics_compiler.ir.graph.container import AestheticGraph
from aesthetics_compiler.ir.graph.canonical import canonical_hash


def _make_graph() -> AestheticGraph:
    g = AestheticGraph()
    g.add_node(AestheticNode(id="n1", kind=NodeKind.ELEMENT, label="red block",
                             aesthetic_scores={"order": 0.8, "complexity": 0.2}))
    g.add_node(AestheticNode(id="n2", kind=NodeKind.ELEMENT, label="blue stripe",
                             aesthetic_scores={"order": 0.5, "complexity": 0.4}))
    g.add_node(AestheticNode(id="z1", kind=NodeKind.ZONE, label="center"))
    g.add_edge(AestheticEdge(src="z1", dst="n1", kind=EdgeKind.CONTAINS))
    g.add_edge(AestheticEdge(src="n1", dst="n2", kind=EdgeKind.CONTRASTS))
    return g


def test_graph_construction():
    g = _make_graph()
    assert len(g.nodes) == 3
    assert len(g.edges) == 2


def test_node_lookup():
    g = _make_graph()
    n = g.node("n1")
    assert n is not None
    assert n.label == "red block"
    assert g.node("missing") is None


def test_neighbors():
    g = _make_graph()
    nbrs = g.neighbors("n1")
    ids = {n.id for n in nbrs}
    assert "z1" in ids
    assert "n2" in ids


def test_element_nodes():
    g = _make_graph()
    elems = g.element_nodes()
    assert len(elems) == 2


def test_hash_deterministic():
    g1 = _make_graph()
    g2 = _make_graph()
    assert canonical_hash(g1) == canonical_hash(g2)


def test_hash_changes_with_modification():
    g1 = _make_graph()
    g2 = _make_graph()
    g2.add_node(AestheticNode(id="n3", kind=NodeKind.ELEMENT, label="new"))
    assert canonical_hash(g1) != canonical_hash(g2)

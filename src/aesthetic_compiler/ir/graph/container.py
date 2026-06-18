from __future__ import annotations
from pydantic import BaseModel
from aesthetic_compiler.ir.graph.schema import AestheticNode, AestheticEdge, NodeKind, EdgeKind


class AestheticGraph(BaseModel):
    nodes: dict[str, AestheticNode] = {}
    edges: list[AestheticEdge] = []
    graph_hash: str | None = None

    def add_node(self, node: AestheticNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: AestheticEdge) -> None:
        self.edges.append(edge)

    def node(self, node_id: str) -> AestheticNode | None:
        return self.nodes.get(node_id)

    def neighbors(self, node_id: str) -> list[AestheticNode]:
        ids = {e.dst for e in self.edges if e.src == node_id}
        ids |= {e.src for e in self.edges if e.dst == node_id}
        return [self.nodes[i] for i in ids if i in self.nodes]

    def edges_between(self, src: str, dst: str) -> list[AestheticEdge]:
        return [e for e in self.edges if (e.src == src and e.dst == dst) or (e.src == dst and e.dst == src)]

    def nodes_of_kind(self, kind: NodeKind) -> list[AestheticNode]:
        return [n for n in self.nodes.values() if n.kind == kind]

    def element_nodes(self) -> list[AestheticNode]:
        return self.nodes_of_kind(NodeKind.ELEMENT)

    def element_pairs(self) -> list[tuple[AestheticNode, AestheticNode]]:
        elems = self.element_nodes()
        return [(elems[i], elems[j]) for i in range(len(elems)) for j in range(i + 1, len(elems))]

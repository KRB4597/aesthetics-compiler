import hashlib
import json
from aesthetics_compiler.ir.graph.container import AestheticGraph


def canonical_hash(graph: AestheticGraph) -> str:
    nodes_sorted = sorted(
        [n.model_dump() for n in graph.nodes.values()],
        key=lambda n: n["id"],
    )
    edges_sorted = sorted(
        [e.model_dump() for e in graph.edges],
        key=lambda e: (e["src"], e["dst"], e["kind"]),
    )
    payload = json.dumps({"nodes": nodes_sorted, "edges": edges_sorted}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

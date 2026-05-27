from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

@router.get("/graph/explore")
async def explore_graph(node: str, depth: int = 2):
    from api.main import graph

    # Simple BFS to find subgraph
    nodes = []
    edges = []
    visited_nodes = set()
    queue = [(node, 0)] # (label, current_depth)

    while queue:
        label, d = queue.pop(0)
        if label in visited_nodes or d > depth:
            continue

        n = graph.get_node(label)
        if not n:
            continue

        visited_nodes.add(label)
        nodes.append({"id": n.id, "label": n.label})

        if d < depth:
            outgoing = graph.get_outgoing_edges(n.id)
            for e in outgoing:
                target_node = graph.store.get_node(e.target_id)
                if target_node:
                    edges.append({
                        "source": n.id,
                        "target": target_node.id,
                        "type": e.edge_type,
                        "strength": e.strength
                    })
                    queue.append((target_node.label, d + 1))

    return {"nodes": nodes, "edges": edges}

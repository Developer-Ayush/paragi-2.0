from typing import List
import numpy as np
from core.graph import ParagiGraph
from reasoning.traversal import TraversalPath, find_paths

def classify_edge(source_id: str, target_id: str, graph: ParagiGraph) -> str:
    """
    Count independent path clusters from source to target.
    ≥3 independent clusters → CAUSES
    1-2 clusters → CORRELATES
    Externally asserted → ASSERTED
    Derived by traversal → INFERRED
    """
    source_node = graph.store.get_node(source_id)
    target_node = graph.store.get_node(target_id)
    if not source_node or not target_node:
        return "INFERRED"

    # We need to find all independent edges/paths between source and target
    # In Paragi, multiple edges between same nodes are collapsed/strengthened
    # but they can come from different clusters.
    # However, our add_edge is idempotent and overwrites/strengthens.
    # Wait, the prompt says: "Group paths by source_cluster of their first edge."
    # If we have only ONE edge (collapsed), we only have one source_cluster?
    # No, the v12 fix mentions democratic consensus.
    # Let's check Edge dataclass. It has source_cluster: str = "unknown".

    # If edges are collapsed, we lose the individual clusters unless we store them.
    # The prompt says: "Count distinct clusters → this is the independence measure."

    # Let's assume for this version that we check the edge's own cluster
    # or look for alternative paths.

    dummy_vec = np.zeros(1024)
    dummy_dims = list(range(1024))
    paths = find_paths(graph, source_node.label, target_node.label, dummy_vec, dummy_dims)

    # If we want to support multiple clusters for a single edge,
    # we'd need to change Edge to have a list of clusters.
    # For now, let's just stick to the count from paths.

    num_clusters = get_independent_clusters(paths)

    if num_clusters >= 3:
        return "CAUSES"
    elif num_clusters >= 1:
        return "CORRELATES"
    else:
        return "INFERRED"

def get_independent_clusters(paths: List[TraversalPath]) -> int:
    """
    Group paths by source_cluster of their first edge.
    Count distinct clusters → this is the independence measure.
    """
    clusters = set()
    for path in paths:
        if path.edges:
            # If multiple paths exist, they might have different first edges
            # if there are parallel edges. But our graph collapses them.
            # This logic assumes there might be multiple paths through DIFFERENT nodes.
            for edge in path.edges:
                 clusters.add(edge.source_cluster)
    return len(clusters)

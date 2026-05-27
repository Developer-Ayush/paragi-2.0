from typing import List
from core.graph import ParagiGraph
from reasoning.traversal import TraversalPath

def classify_edge(source_id: str, target_id: str, graph: ParagiGraph) -> str:
    """
    Count independent path clusters from source to target.
    ≥3 independent clusters → CAUSES
    1-2 clusters → CORRELATES
    Externally asserted → ASSERTED
    Derived by traversal → INFERRED
    """
    # For independent clusters, we need paths between source and target
    # This is slightly different from find_paths which takes labels.
    # We'll use a simplified version for now or assume find_paths can handle it.

    # In a real system, this would be triggered periodically.
    # For now, let's implement the logic.

    # Find all paths (up to some max depth)
    source_node = graph.store.get_node(source_id)
    target_node = graph.store.get_node(target_id)
    if not source_node or not target_node:
        return "INFERRED"

    # query_vector and active_dims are needed for scoring in find_paths,
    # but for classification we just care about path counts.
    # We'll use dummy values.
    import numpy as np
    dummy_vec = np.zeros(1024)
    dummy_dims = list(range(1024))

    paths = [] # In a full implementation, we'd call find_paths
    # But find_paths itself is used for reasoning.
    # Let's assume we have the paths.

    # Mocking for now to follow architecture
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
            clusters.add(path.edges[0].source_cluster)
    return len(clusters)

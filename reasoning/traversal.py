from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np
import config
from core.graph import ParagiGraph
from core.edge import Edge

@dataclass
class TraversalPath:
    nodes: List[str]     # node_ids in order
    edges: List[Edge]    # edges traversed
    score: float = 0.0
    confidence: float = 1.0
    hops: int = 0

def find_paths(
    graph: ParagiGraph,
    source_label: str,
    target_label: str,
    query_vector: np.ndarray,
    active_dims: List[int],
    beam_width: int = config.BEAM_WIDTH,
    max_hops: int = config.MAX_HOPS
) -> List[TraversalPath]:

    source_node = graph.get_node(source_label)
    target_node = graph.get_node(target_label)

    if not source_node or not target_node:
        return []

    from reasoning.scoring import score_path

    # beam element: TraversalPath
    beam = [TraversalPath(nodes=[source_node.id], edges=[], hops=0)]
    completed_paths = []

    for hop in range(max_hops):
        new_beam = []
        for path in beam:
            last_node_id = path.nodes[-1]
            if last_node_id == target_node.id and path.hops > 0:
                # This should not happen in expansion but just in case
                continue

            outgoing_edges = graph.get_outgoing_edges(last_node_id)
            for edge in outgoing_edges:
                if edge.target_id in path.nodes:
                    continue # Cycle detection

                new_path = TraversalPath(
                    nodes=path.nodes + [edge.target_id],
                    edges=path.edges + [edge],
                    hops=path.hops + 1
                )
                new_path.score = score_path(new_path, query_vector, active_dims, graph)

                if edge.target_id == target_node.id:
                    completed_paths.append(new_path)
                    if new_path.confidence > config.MIN_CONFIDENCE_EARLY_STOP:
                         # For simplicity, we'll collect all and return, but early stop could be implemented
                         pass
                else:
                    new_beam.append(new_path)

        if not new_beam:
            break

        # Keep top beam_width
        new_beam.sort(key=lambda x: x.score, reverse=True)
        beam = new_beam[:beam_width]

    completed_paths.sort(key=lambda x: x.score, reverse=True)
    return completed_paths

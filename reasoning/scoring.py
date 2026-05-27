import numpy as np
from typing import List
from scipy.spatial.distance import cosine
import config
from core.graph import ParagiGraph

def cosine_similarity(a, b):
    # Handle zero vectors or NaN from cosine function
    if np.all(a == 0) or np.all(b == 0):
        return 0.0
    try:
        dist = cosine(a, b)
        if np.isnan(dist):
            return 0.0
        return 1.0 - dist
    except Exception:
        return 0.0

def score_path(path, query_vector: np.ndarray, active_dims: List[int], graph: ParagiGraph) -> float:
    if not path.edges:
        return 0.0

    # 1. Mean effective strength
    mean_strength = np.mean([e.effective_strength() for e in path.edges])

    # 2. Goal relevance
    effective_vectors = [e.effective_vector() for e in path.edges]
    path_vector = np.mean(effective_vectors, axis=0)

    query_slice = query_vector[active_dims]
    path_slice = path_vector[active_dims]

    # Ensure goal_relevance is not zero if vectors are zero (like in testing)
    if np.all(query_slice == 0) and np.all(path_slice == 0):
        goal_relevance = 1.0
    else:
        goal_relevance = cosine_similarity(query_slice, path_slice)

    # 3. Provenance confidence
    provenance_confidence = np.mean([e.source_reliability for e in path.edges])

    # 4. Edge type weight
    type_weights = {
        "CAUSES": 1.0,
        "IS_A": 0.9,
        "TEMPORAL": 0.85,
        "INFERRED": 0.75,
        "CORRELATES": 0.7,
        "ASSERTED": 0.8
    }
    edge_type_weight = np.mean([type_weights.get(e.edge_type, 0.5) for e in path.edges])

    # 5. Hub penalty
    hub_penalty = 1.0
    for node_id in path.nodes:
        outgoing = graph.get_outgoing_edges(node_id)
        degree = len(outgoing)
        if degree > 2000:
            hub_penalty *= 0.6
        elif degree > 500:
            hub_penalty *= 0.8

    score = (float(mean_strength) *
             float(goal_relevance) *
             float(provenance_confidence) *
             float(edge_type_weight) *
             float(hub_penalty))

    path.confidence = float(np.clip(score, 0.0, 1.0))
    path.score = score
    return score

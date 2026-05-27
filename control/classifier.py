from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import config

@dataclass
class QueryClassification:
    primary_region: Tuple[int, int]    # e.g., FACTUAL_DIMS
    active_dims: List[int]             # flat list of active dim indices
    complexity_score: float            # 0.0 - 1.0
    activation_budget: int             # how many dims to activate

def classify_query(query: str, encoder_vector: np.ndarray) -> QueryClassification:
    """
    Complexity score = f(ambiguity, unknown_concept_ratio, estimated_hop_depth)
    """
    query_lower = query.lower()

    # 1. Estimated hop depth
    if query_lower.startswith(("why", "how")):
        estimated_hop_depth = 5
    elif any(word in query_lower for word in ["cause", "lead to", "result in"]):
        estimated_hop_depth = 4
    else:
        estimated_hop_depth = 2

    # 2. Ambiguity (entropy of encoder_vector)
    # Only look at the active encoder region
    active_region = encoder_vector[config.ENCODER_ACTIVE_START:config.ENCODER_ACTIVE_END+1]
    if np.sum(np.abs(active_region)) > 0:
        # Simple measure of how spread out the activation is
        normalized = np.abs(active_region) / np.sum(np.abs(active_region))
        entropy = -np.sum(normalized * np.log(normalized + 1e-10))
        ambiguity = float(np.clip(entropy / 5.0, 0.0, 1.0))
    else:
        ambiguity = 0.5

    # 3. Complexity score
    # weight them: depth 40%, ambiguity 40%, unknown concepts 20% (skipped for now)
    complexity_score = (estimated_hop_depth / config.MAX_HOPS) * 0.5 + ambiguity * 0.5
    complexity_score = float(np.clip(complexity_score, 0.0, 1.0))

    # 4. Activation budget
    if complexity_score < 0.3:
        activation_budget = 20
    elif complexity_score < 0.7:
        activation_budget = 75
    else:
        activation_budget = 150

    return QueryClassification(
        primary_region=config.FACTUAL_DIMS,
        active_dims=[], # populated by get_active_dims
        complexity_score=complexity_score,
        activation_budget=activation_budget
    )

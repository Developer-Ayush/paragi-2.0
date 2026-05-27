from typing import List
from control.classifier import QueryClassification
import config

def get_active_dims(classification: QueryClassification) -> List[int]:
    """
    Returns the list of dim indices to use for this query.
    Always includes dims 480-669 (factual + causal + encoder-active region).
    Adds contextual/cognitive dims based on complexity.
    """
    # Base mandatory dims
    base_dims = set(range(config.ENCODER_ACTIVE_START, config.ENCODER_ACTIVE_END + 1))

    # Based on budget, add more from other regions
    extra_budget = max(0, classification.activation_budget - len(base_dims))

    if extra_budget > 0:
        # Add from contextual modulation
        context_start, context_end = config.CONTEXTUAL_MODULATION_DIMS
        for i in range(context_start, min(context_end, context_start + extra_budget)):
            base_dims.add(i)

    # Always include factual/causal ranges as they are core
    base_dims.update(range(config.FACTUAL_DIMS[0], config.FACTUAL_DIMS[1] + 1))
    base_dims.update(range(config.CAUSAL_DIMS[0], config.CAUSAL_DIMS[1] + 1))

    return sorted(list(base_dims))

def update_control_block(edge, classification: QueryClassification, success: bool):
    """
    After a successful traversal, update the control block dims of traversed edges.
    """
    if not success:
        return

    # LEARNING_RATE_DIMS: adjust per-region learning signal
    # This is a placeholder for actual vector modification
    pass

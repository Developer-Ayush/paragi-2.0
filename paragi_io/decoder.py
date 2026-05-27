from typing import List, Dict
from reasoning.traversal import TraversalPath
import config

EDGE_TYPE_TEMPLATES = {
    "CAUSES":     "{source} causes {target}.",
    "CORRELATES": "{source} is associated with {target}.",
    "IS_A":       "{source} is a type of {target}.",
    "TEMPORAL":   "{source} happens before {target}.",
    "INFERRED":   "{source} likely leads to {target}.",
    "ASSERTED":   "{source} is related to {target}.",
}

def decode_path(path: TraversalPath, node_labels: Dict[str, str]) -> str:
    """
    Convert a traversal path to a readable answer.
    """
    if not path.edges:
        return "I don't know yet."

    parts = []
    for i, edge in enumerate(path.edges):
        source_label = node_labels.get(edge.source_id, "unknown")
        target_label = node_labels.get(edge.target_id, "unknown")
        template = EDGE_TYPE_TEMPLATES.get(edge.edge_type, "{source} is related to {target}.")
        sentence = template.format(source=source_label, target=target_label)

        if i == 0:
            parts.append(sentence)
        else:
            # Chain with "which" or "therefore"
            parts.append(f"which {sentence.lower()}")

    answer = " ".join(parts)
    # Capitalize first letter if it was chained
    answer = answer[0].upper() + answer[1:]

    return f"{answer} (confidence: {path.confidence:.2f})"

def decode_no_path(query: str) -> str:
    """Used when no path found. Acknowledges the gap."""
    return f"I couldn't find a direct connection for '{query}'. I'm looking into it."

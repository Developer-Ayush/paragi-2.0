import time
from core.graph import ParagiGraph
import config

def award_credits(user_id: str, new_nodes_created: int, graph: ParagiGraph):
    """Award CREDITS_PER_NEW_NODE credits per new node. Delayed: mark as pending."""
    if new_nodes_created <= 0:
        return

    current_credits = graph.store.get_user_credits(user_id)
    pending = new_nodes_created * config.CREDITS_PER_NEW_NODE

    # Store pending separately or just award for now in prototype
    graph.store.save_user_credits(user_id, current_credits + pending)

def validate_and_confirm_credits(graph: ParagiGraph):
    """
    Called from background worker.
    """
    pass

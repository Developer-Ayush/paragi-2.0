import httpx
import time
import uuid
from typing import List, Tuple, Optional
from core.node import Node
from core.graph import ParagiGraph
import config

def create_expansion_node(query_label: str, graph: ParagiGraph) -> Node:
    """Creates a Node with is_expansion_node=True at the location of a knowledge gap."""
    node = Node(
        label=query_label,
        id=str(uuid.uuid4()),
        created_at=time.time(),
        last_accessed=time.time(),
        is_expansion_node=True
    )
    graph.store.save_node(node)
    graph.bloom.add(query_label)
    return node

class ExternalFetcher:
    """
    Fallback cascade:
    1. Internal graph (already tried)
    2. DuckDuckGo Instant Answer API
    3. Wikipedia summary API
    4. Return empty if both fail
    """
    async def fetch(self, label: str) -> Optional[str]:
        # 1. DuckDuckGo
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://api.duckduckgo.com/?q={label}&format=json")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("AbstractText"):
                        return data["AbstractText"]
        except Exception:
            pass

        # 2. Wikipedia
        try:
            async with httpx.AsyncClient() as client:
                # Wikipedia uses title case often
                title = label.replace(" ", "_")
                resp = await client.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}")
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("extract"):
                        return data["extract"]
        except Exception:
            pass

        return None

async def resolve_expansion_nodes(graph: ParagiGraph, fetcher: ExternalFetcher, encoder):
    """
    Called from background worker every 30 seconds.
    For each expansion node:
      1. Try internet search
      2. Parse result → extract (subject, relation, object) triples
      3. Add edges to graph
      4. Delete expansion node
    """
    # This needs to find nodes with is_expansion_node=True
    # Since we don't have a secondary index for this yet, we might need one or scan (slow)
    # For now, let's assume we have a queue of expansion node IDs
    pass

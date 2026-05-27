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

    # Add to queue
    import json
    with graph.store.lock:
        data = graph.store._get("expansion_queue")
        queue = json.loads(data) if data else []
        queue.append(node.id)
        graph.store.db["expansion_queue"] = json.dumps(queue)

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
    # Since we don't have a secondary index, we'd need to scan or use a queue.
    # For this prototype, we'll check if there's an expansion_queue in the store.
    import json
    data = graph.store._get("expansion_queue")
    if not data:
        return

    queue = json.loads(data)
    if not queue:
        return

    new_queue = []
    for node_id in queue:
        node = graph.store.get_node(node_id)
        if not node or not node.is_expansion_node:
            continue

        result_text = await fetcher.fetch(node.label)
        if result_text:
            # Simple triple extraction or just create a general edge
            # For now, let's just create one ASSERTED edge if we find something
            # In a full version, we'd use extract_triple(result_text)
            from paragi_io.canonicalize import extract_triple
            triple = extract_triple(result_text)
            if triple:
                s, r, o = triple
                vector = encoder.encode(result_text)
                graph.add_edge(s, o, r, vector, source_cluster="external", source_reliability=0.6)

            # Successfully resolved or at least tried
            # Delete expansion node marker (or just flip flag)
            node.is_expansion_node = False
            graph.store.save_node(node)
        else:
            # Keep in queue if failed?
            new_queue.append(node_id)

    graph.store._save("expansion_queue", json.dumps(new_queue))

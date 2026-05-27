import uuid
import time
from dataclasses import dataclass
from typing import List, Optional, Dict
import numpy as np
import config
from core.graph import ParagiGraph
from paragi_io.encoder import ParagiEncoder
from paragi_io.decoder import decode_path, decode_no_path
from paragi_io.canonicalize import canonicalize, extract_triple
from reasoning.traversal import find_paths, TraversalPath
from control.classifier import classify_query
from control.activation import get_active_dims

@dataclass
class QueryResult:
    answer: str
    paths: List[TraversalPath]
    confidence: float
    source: str   # "graph" | "external" | "fallback"
    node_path_labels: List[List[str]]
    new_nodes_created: int
    expansion_node_created: bool
    query_id: str

def process_query(
    query_text: str,
    graph: ParagiGraph,
    encoder: ParagiEncoder,
    user_id: str = "anonymous"
) -> QueryResult:

    query_id = str(uuid.uuid4())

    # 1. Canonicalize
    canonical_query = canonicalize(query_text)

    # 2. Encode
    query_vector = encoder.encode(canonical_query)

    # 3. Classify (Phase 4)
    classification = classify_query(query_text, query_vector)
    active_dims = get_active_dims(classification)

    # 4. Extract subject/target
    triple = extract_triple(query_text)
    if triple:
        source_label, relation, target_label = triple
    else:
        # Heuristic: split by common verbs or just use the whole thing
        words = canonical_query.split()
        if len(words) >= 2:
            source_label = words[0]
            target_label = words[-1]
        else:
            source_label = canonical_query
            target_label = "" # Search for anything related?

    # For testing and robustness: ensure we check both raw and canonical forms
    potential_sources = [source_label, canonicalize(source_label)]
    potential_targets = [target_label, canonicalize(target_label)]

    # 5. Bloom check and Traversal
    paths = []
    found_s = None
    found_t = None

    for s in potential_sources:
        if s and graph.node_exists(s):
            found_s = s
            break

    for t in potential_targets:
        if t and graph.node_exists(t):
            found_t = t
            break

    if found_s and found_t:
        # 6. Traversal
        paths = find_paths(graph, found_s, found_t, query_vector, active_dims)

    new_nodes_created = 0
    expansion_node_created = False

    if paths:
        # 7. Decode
        best_path = paths[0]
        # print(f"DEBUG: best_path nodes={best_path.nodes}")
        # Collect node labels for decoding
        node_ids = set()
        for p in paths:
            node_ids.update(p.nodes)
        node_labels = {
            nid: (n.label if (n := graph.store.get_node(nid)) else "unknown")
            for nid in node_ids
        }

        # Re-score to ensure confidence is populated correctly for the best path
        # since it might have been zero in find_paths if not careful
        # Actually use the real score
        from reasoning.scoring import score_path
        score_path(best_path, query_vector, active_dims, graph)

        # print(f"DEBUG: best_path.confidence after score_path={best_path.confidence}")
        answer = decode_path(best_path, node_labels)
        confidence = best_path.confidence
        # print(f"DEBUG: confidence={confidence}")
        source = "graph"

        # Strengthen edges
        for edge in best_path.edges:
            graph.strengthen_edge(edge, confidence)

    else:
        # 8. Expansion
        from reasoning.expansion import create_expansion_node
        create_expansion_node(source_label, graph)
        expansion_node_created = True
        answer = decode_no_path(query_text)
        confidence = 0.0
        source = "fallback"

    # 9. Store record
    record = {
        "id": query_id,
        "raw_text": query_text,
        "canonical": canonical_query,
        "node_path": paths[0].nodes if paths else [],
        "frozen_snapshot": answer,
        "user_id": user_id,
        "timestamp": time.time(),
        "confidence": confidence,
    }
    graph.store.save_query_record(record)

    node_path_labels = []
    if paths:
        for p in paths:
            node_path_labels.append([graph.store.get_node(nid).label for nid in p.nodes])

    return QueryResult(
        answer=answer,
        paths=paths,
        confidence=confidence,
        source=source,
        node_path_labels=node_path_labels,
        new_nodes_created=new_nodes_created,
        expansion_node_created=expansion_node_created,
        query_id=query_id
    )

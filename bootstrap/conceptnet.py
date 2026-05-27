import json
import logging
from typing import Generator, Tuple
import config
from core.graph import ParagiGraph
from paragi_io.encoder import ParagiEncoder
from paragi_io.canonicalize import canonicalize, semantic_distance

CONCEPTNET_RELATION_MAP = {
    "/r/Causes": "CAUSES",
    "/r/IsA": "IS_A",
    "/r/RelatedTo": "CORRELATES",
    "/r/HasPrerequisite": "TEMPORAL",
    "/r/MotivatedByGoal": "INFERRED",
    "/r/UsedFor": "CORRELATES",
    "/r/CapableOf": "CAUSES",
    "/r/PartOf": "IS_A",
    "/r/AtLocation": "CORRELATES",
    "/r/HasProperty": "IS_A",
}

def parse_conceptnet_csv(csv_path: str, language: str = "en") -> Generator[Tuple[str, str, str, float], None, None]:
    """
    Generator that yields (subject, relation, object, weight) tuples.
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue

            uri, rel_uri, sub_uri, obj_uri, meta_json = parts

            # Filter language
            if not (sub_uri.startswith(f"/c/{language}/") and obj_uri.startswith(f"/c/{language}/")):
                continue

            # Extract names
            # /c/en/fire/n -> fire
            sub = sub_uri.split('/')[3].replace('_', ' ')
            obj = obj_uri.split('/')[3].replace('_', ' ')

            rel = CONCEPTNET_RELATION_MAP.get(rel_uri, "CORRELATES")

            try:
                meta = json.loads(meta_json)
                weight = float(meta.get('weight', 1.0))
            except Exception:
                weight = 1.0

            if weight < 1.0:
                continue

            yield sub, rel, obj, weight

def ingest_conceptnet(graph: ParagiGraph, encoder: ParagiEncoder,
                       csv_path: str, max_edges: int = 500_000):
    """
    Read ConceptNet CSV and ingest.
    """
    print(f"Starting ConceptNet ingestion from {csv_path} (max {max_edges} edges)...")

    gen = parse_conceptnet_csv(csv_path)

    # Log first 5 samples for verification
    print("Samples from parser:")
    samples = []
    for _ in range(5):
        try:
            samples.append(next(gen))
        except StopIteration:
            break

    for s, r, o, w in samples:
        print(f"  {s} --[{r}]--> {o} (weight: {w})")

    count = 0
    for sub, rel, obj, weight in parse_conceptnet_csv(csv_path): # Restart or chain
        if count >= max_edges:
            break

        sub_c = canonicalize(sub)
        obj_c = canonicalize(obj)

        # In a real run, we might want to check semantic_distance,
        # but for bootstrap speed we skip or use a cache.

        # Encode context: "sub rel obj"
        vector = encoder.encode(f"{sub} {rel.lower().replace('_', ' ')} {obj}")

        graph.add_edge(
            source_label=sub_c,
            target_label=obj_c,
            edge_type=rel,
            vector=vector,
            source_cluster="conceptnet",
            source_reliability=float(min(1.0, weight / 5.0))
        )

        count += 1
        if count % 10000 == 0:
            print(f"Ingested {count} edges...")

    print(f"Ingestion complete. Total edges: {count}")

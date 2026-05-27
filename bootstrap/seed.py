import os
from core.graph import ParagiGraph
from paragi_io.encoder import ParagiEncoder
from bootstrap.conceptnet import ingest_conceptnet
import config

def run_bootstrap(graph: ParagiGraph, encoder: ParagiEncoder):
    """
    1. Check if ConceptNet CSV exists
    2. Call ingest_conceptnet
    """
    csv_path = config.CONCEPTNET_CSV_PATH
    if not os.path.exists(csv_path):
        print(f"ConceptNet CSV not found at {csv_path}.")
        print("Please run: python scripts/download_conceptnet.py")
        return

    ingest_conceptnet(graph, encoder, csv_path, max_edges=500000)

    print(f"Bootstrap complete. Nodes: {graph.total_nodes()}, Edges: {graph.total_edges()}")

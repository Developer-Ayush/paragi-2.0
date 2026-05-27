import pytest
import numpy as np
from core.node import Node
from core.edge import Edge
from core.graph import ParagiGraph
from storage.bloom import BloomFilter
from storage.rocksdb_store import RocksDBStore
from reasoning.traversal import find_paths
import os
import shutil

@pytest.fixture
def graph():
    path = "./data/test_traversal_db"
    if os.path.exists(path):
        shutil.rmtree(path)
    store = RocksDBStore(path)
    bloom = BloomFilter(1000, 0.001)
    g = ParagiGraph(store, bloom)
    yield g
    store.close()
    if os.path.exists(path):
        shutil.rmtree(path)

def test_chain_traversal(graph):
    # fire → temperature → heat → burn
    vector = np.zeros(1024)
    graph.add_edge("fire", "temperature", "CAUSES", vector)
    graph.add_edge("temperature", "heat", "CAUSES", vector)
    graph.add_edge("heat", "burn", "CAUSES", vector)

    paths = find_paths(graph, "fire", "burn", vector, list(range(1024)))
    assert len(paths) > 0
    assert paths[0].hops == 3
    assert "burn" in [graph.store.get_node(nid).label for nid in paths[0].nodes]

def test_cycle_detection(graph):
    vector = np.zeros(1024)
    graph.add_edge("A", "B", "CAUSES", vector)
    graph.add_edge("B", "C", "CAUSES", vector)
    graph.add_edge("C", "A", "CAUSES", vector)

    # Try to find path A -> D (doesn't exist)
    # Just ensure it doesn't infinite loop
    paths = find_paths(graph, "A", "D", vector, list(range(1024)))
    assert len(paths) == 0

import pytest
import numpy as np
from core.graph import ParagiGraph
from storage.bloom import BloomFilter
from storage.rocksdb_store import RocksDBStore
from paragi_io.encoder import ParagiEncoder
from paragi_io.pipeline import process_query
import os
import shutil

@pytest.fixture
def env():
    path = "./data/test_pipeline_db"
    if os.path.exists(path):
        shutil.rmtree(path)
    store = RocksDBStore(path)
    bloom = BloomFilter(1000, 0.001)
    graph = ParagiGraph(store, bloom)
    encoder = ParagiEncoder()
    yield graph, encoder
    store.close()
    if os.path.exists(path):
        shutil.rmtree(path)

def test_full_pipeline(env):
    graph, encoder = env
    vector = encoder.encode("fire burn")
    graph.add_edge("fire", "burn", "CAUSES", vector)

    result = process_query("does fire burn?", graph, encoder)
    assert "fire causes burn" in result.answer.lower()
    assert result.confidence >= 0
    assert result.source == "graph"

def test_unknown_query(env):
    graph, encoder = env
    result = process_query("what is gleepglop?", graph, encoder)
    assert "gleepglop" in result.answer.lower()
    assert result.expansion_node_created is True
    assert result.source == "fallback"

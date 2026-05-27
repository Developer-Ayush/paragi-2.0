import pytest
import numpy as np
import os
import shutil
from core.node import Node
from core.edge import Edge
from storage.bloom import BloomFilter
from storage.rocksdb_store import RocksDBStore
from core.graph import ParagiGraph
import config

@pytest.fixture
def temp_db():
    path = "./data/test_db"
    if os.path.exists(path):
        shutil.rmtree(path)
    store = RocksDBStore(path)
    yield store
    store.close()
    if os.path.exists(path):
        shutil.rmtree(path)

def test_node_storage(temp_db):
    node = Node(label="test", id="123", created_at=1000, last_accessed=1000)
    temp_db.save_node(node)
    retrieved = temp_db.get_node("123")
    assert retrieved.label == "test"
    assert retrieved.id == "123"

def test_bloom_filter():
    bloom = BloomFilter(capacity=1000, error_rate=0.001)
    bloom.add("apple")
    assert "apple" in bloom
    assert "banana" not in bloom

def test_edge_storage(temp_db):
    vector = np.random.rand(1024).astype(np.float32)
    edge = Edge(source_id="s", target_id="t", edge_type="IS_A", vector=vector, strength=0.8, id="e1")
    temp_db.save_edge(edge)
    retrieved = temp_db.get_edge("e1")
    assert retrieved.edge_type == "IS_A"
    assert np.allclose(retrieved.vector, vector)

def test_graph_idempotency(temp_db):
    bloom = BloomFilter(capacity=1000, error_rate=0.001)
    graph = ParagiGraph(temp_db, bloom)
    vector = np.zeros(1024)
    e1 = graph.add_edge("A", "B", "CAUSES", vector)
    e2 = graph.add_edge("A", "B", "CAUSES", vector)
    assert e1.id == e2.id
    assert graph.total_edges() == 1

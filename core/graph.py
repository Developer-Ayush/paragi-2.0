import time
import uuid
import hashlib
from typing import Optional, List, Tuple
import numpy as np
from core.node import Node
from core.edge import Edge
from storage.rocksdb_store import RocksDBStore
from storage.bloom import BloomFilter
import config

class ParagiGraph:
    def __init__(self, store: RocksDBStore, bloom: BloomFilter):
        self.store = store
        self.bloom = bloom

    def node_exists(self, label: str) -> bool:
        if label in self.bloom:
            return self.store.get_node_by_label(label) is not None
        return False

    def get_or_create_node(self, label: str) -> Tuple[Node, bool]:
        node = self.store.get_node_by_label(label)
        if node:
            return node, False

        node = Node(
            label=label,
            id=str(uuid.uuid4()),
            created_at=time.time(),
            last_accessed=time.time()
        )
        self.store.save_node(node)
        self.bloom.add(label)

        # Increment total nodes count
        with self.store.lock:
            count = self.store._get("total_nodes_count")
            new_count = (int(count) if count else 0) + 1
            self.store.db["total_nodes_count"] = str(new_count)

        return node, True

    def _generate_edge_id(self, source_id: str, target_id: str, edge_type: str) -> str:
        key = f"{source_id}:{target_id}:{edge_type}"
        return hashlib.sha256(key.encode()).hexdigest()

    def add_edge(self, source_label: str, target_label: str,
                 edge_type: str, vector: np.ndarray,
                 source_cluster: str = "unknown",
                 source_reliability: float = 0.5) -> Edge:

        source_node, _ = self.get_or_create_node(source_label)
        target_node, _ = self.get_or_create_node(target_label)

        edge_id = self._generate_edge_id(source_node.id, target_node.id, edge_type)
        existing_edge = self.store.get_edge(edge_id)

        if existing_edge:
            # Idempotency: strengthen existing edge
            existing_edge.update_strength(path_confidence=1.0, retrieval_success=True, elapsed_hours=0)
            # Optionally update vector or other metadata
            existing_edge.source_reliability = (existing_edge.source_reliability + source_reliability) / 2.0
            self.store.save_edge(existing_edge)
            return existing_edge

        edge = Edge(
            source_id=source_node.id,
            target_id=target_node.id,
            edge_type=edge_type,
            vector=vector.astype(np.float32),
            strength=config.INITIAL_STRENGTH,
            last_activated=time.time(),
            last_updated=time.time(),
            created_at=time.time(),
            source_cluster=source_cluster,
            source_reliability=source_reliability,
            id=edge_id
        )
        self.store.save_edge(edge)

        # Increment total edges count
        with self.store.lock:
            count = self.store._get("total_edges_count")
            new_count = (int(count) if count else 0) + 1
            self.store.db["total_edges_count"] = str(new_count)

        return edge

    def get_node(self, label: str) -> Optional[Node]:
        return self.store.get_node_by_label(label)

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        return self.store.get_outgoing_edges(node_id)

    def strengthen_edge(self, edge: Edge, confidence: float):
        edge.update_strength(path_confidence=confidence, retrieval_success=True, elapsed_hours=0)
        self.store.save_edge(edge)

    def total_nodes(self) -> int:
        count = self.store._get("total_nodes_count")
        return int(count) if count else 0

    def total_edges(self) -> int:
        count = self.store._get("total_edges_count")
        return int(count) if count else 0

import json
import threading
import os
import numpy as np
from typing import List, Optional, Dict, Any
from rocksdict import Rdict, Options
import config
from core.node import Node
from core.edge import Edge

class RocksDBStore:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = Rdict(path, Options())
        self.lock = threading.RLock()

    def _save(self, key: str, value: Any):
        with self.lock:
            self.db[key] = value

    def _get(self, key: str) -> Optional[Any]:
        try:
            return self.db[key]
        except KeyError:
            return None

    def save_node(self, node: Node):
        self._save(f"nodes:{node.id}", json.dumps(node.to_dict()))
        self._save(f"label_index:{node.label}", node.id)

    def get_node(self, node_id: str) -> Optional[Node]:
        data = self._get(f"nodes:{node_id}")
        if data:
            return Node.from_dict(json.loads(data))
        return None

    def get_node_by_label(self, label: str) -> Optional[Node]:
        node_id = self._get(f"label_index:{label}")
        if node_id:
            return self.get_node(node_id)
        return None

    def save_edge(self, edge: Edge):
        edge_dict = edge.to_dict()
        # For efficiency, we could store vector as bytes,
        # but since Edge.to_dict() already exists, we'll stick to it for now
        # and optimize later if needed. The prompt mentioned vector as bytes for efficiency.
        # Let's override vector to bytes here.
        vector_bytes = edge.vector.astype(np.float32).tobytes()
        edge_dict['vector'] = vector_bytes.hex() # Convert to hex string for JSON compatibility if needed,
        # or use a format that supports bytes. rocksdict supports bytes values.

        # Actually, let's store the whole edge dict but handle the vector separately if we want max efficiency.
        # But rocksdict can store arbitrary objects if they are serializable.
        # Let's stick to JSON for now for the rest and hex for vector.

        self._save(f"edges:{edge.id}", json.dumps(edge_dict))

        # Update outgoing/incoming indices
        with self.lock:
            outgoing = self._get(f"outgoing:{edge.source_id}")
            outgoing_list = json.loads(outgoing) if outgoing else []
            if edge.id not in outgoing_list:
                outgoing_list.append(edge.id)
                self.db[f"outgoing:{edge.source_id}"] = json.dumps(outgoing_list)

            incoming = self._get(f"incoming:{edge.target_id}")
            incoming_list = json.loads(incoming) if incoming else []
            if edge.id not in incoming_list:
                incoming_list.append(edge.id)
                self.db[f"incoming:{edge.target_id}"] = json.dumps(incoming_list)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        data = self._get(f"edges:{edge_id}")
        if data:
            edge_dict = json.loads(data)
            edge_dict['vector'] = np.frombuffer(bytes.fromhex(edge_dict['vector']), dtype=np.float32)
            return Edge.from_dict(edge_dict)
        return None

    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        data = self._get(f"outgoing:{node_id}")
        if not data:
            return []
        edge_ids = json.loads(data)
        return [e for e_id in edge_ids if (e := self.get_edge(e_id))]

    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        data = self._get(f"incoming:{node_id}")
        if not data:
            return []
        edge_ids = json.loads(data)
        return [e for e_id in edge_ids if (e := self.get_edge(e_id))]

    def delete_edge(self, edge_id: str):
        edge = self.get_edge(edge_id)
        if not edge:
            return
        with self.lock:
            del self.db[f"edges:{edge_id}"]

            outgoing = self._get(f"outgoing:{edge.source_id}")
            if outgoing:
                outgoing_list = json.loads(outgoing)
                if edge_id in outgoing_list:
                    outgoing_list.remove(edge_id)
                    self.db[f"outgoing:{edge.source_id}"] = json.dumps(outgoing_list)

            incoming = self._get(f"incoming:{edge.target_id}")
            if incoming:
                incoming_list = json.loads(incoming)
                if edge_id in incoming_list:
                    incoming_list.remove(edge_id)
                    self.db[f"incoming:{edge.target_id}"] = json.dumps(incoming_list)

    def save_query_record(self, record: dict):
        self._save(f"query_history:{record['id']}", json.dumps(record))
        # Keep track of history IDs
        with self.lock:
            history = self._get("history_ids")
            history_list = json.loads(history) if history else []
            history_list.append(record['id'])
            self.db["history_ids"] = json.dumps(history_list)

    def get_query_record(self, query_id: str) -> Optional[dict]:
        data = self._get(f"query_history:{query_id}")
        if data:
            return json.loads(data)
        return None

    def get_query_history(self, limit: int) -> List[dict]:
        history = self._get("history_ids")
        if not history:
            return []
        history_list = json.loads(history)
        results = []
        for h_id in history_list[-limit:]:
            record = self.get_query_record(h_id)
            if record:
                results.append(record)
        return results[::-1]

    def save_user_credits(self, user_id: str, credits: int):
        self._save(f"user_credits:{user_id}", str(credits))

    def get_user_credits(self, user_id: str) -> int:
        data = self._get(f"user_credits:{user_id}")
        return int(data) if data else 0

    def close(self):
        self.db.close()

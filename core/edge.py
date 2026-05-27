from dataclasses import dataclass, field
import numpy as np
import time
from math import exp, log1p
from typing import Dict, Any, List
import config

@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: str   # CAUSES | CORRELATES | IS_A | TEMPORAL | INFERRED | ASSERTED
    vector: np.ndarray   # float32[1024]

    # Dual-layer strength model (v12)
    strength: float        # global scalar salience
    emotional_weight: float = 0.0
    recall_count: int = 0
    stability: float = 0.5

    # Lazy decay timestamps
    last_activated: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    # Provenance (v12 democratic consensus fix)
    source_id_provenance: str = "unknown"
    source_cluster: str = "unknown"
    source_reliability: float = 0.5
    ingestion_chain: str = ""

    id: str = ""   # uuid4 or hash(source_id + target_id + edge_type)

    def effective_strength(self) -> float:
        delta_t_hours = (time.time() - self.last_activated) / 3600.0
        global_decay = 0.005
        effective = config.STRENGTH_FLOOR + (self.strength - config.STRENGTH_FLOOR) * exp(-global_decay * delta_t_hours)
        return max(config.STRENGTH_FLOOR, effective)

    def effective_vector(self) -> np.ndarray:
        delta_t_hours = (time.time() - self.last_updated) / 3600.0
        result = self.vector.copy()
        for (dim_start, dim_end), rate in config.DECAY_RATES.items():
            factor = exp(-rate * delta_t_hours)
            result[dim_start:dim_end+1] *= factor
        return result

    def update_strength(self, path_confidence: float, retrieval_success: bool, elapsed_hours: float):
        S = path_confidence
        R = 1.0 if retrieval_success else 0.0
        D = elapsed_hours * 0.005
        eta = min(0.10 + 0.05 * log1p(self.recall_count), 0.80)

        delta_strength = eta * (S - self.strength) + 0.1 * R - 0.05 * D
        self.strength = float(np.clip(self.strength + delta_strength, config.STRENGTH_FLOOR, 1.0))
        self.recall_count += 1
        self.last_activated = time.time()
        self.last_updated = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type,
            "vector": self.vector.tolist(),
            "strength": self.strength,
            "emotional_weight": self.emotional_weight,
            "recall_count": self.recall_count,
            "stability": self.stability,
            "last_activated": self.last_activated,
            "last_updated": self.last_updated,
            "created_at": self.created_at,
            "source_id_provenance": self.source_id_provenance,
            "source_cluster": self.source_cluster,
            "source_reliability": self.source_reliability,
            "ingestion_chain": self.ingestion_chain,
            "id": self.id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        data = data.copy()
        data['vector'] = np.array(data['vector'], dtype=np.float32)
        return cls(**data)

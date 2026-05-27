from dataclasses import dataclass, field
import time
from typing import Dict, Any

@dataclass
class Node:
    label: str                          # human-readable concept name
    id: str                             # uuid4 or bloom-hash
    created_at: float
    last_accessed: float
    access_count: int = 0
    is_expansion_node: bool = False     # True = knowledge gap marker

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "id": self.id,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "is_expansion_node": self.is_expansion_node
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        return cls(**data)

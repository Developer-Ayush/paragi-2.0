import numpy as np
import os
from fastembed import TextEmbedding
import config

class ParagiEncoder:
    def __init__(self):
        self.model = TextEmbedding("BAAI/bge-small-en-v1.5")
        self.projection_path = "./data/projection.npz"
        self._load_or_save_projection()

    def _xavier_init(self, shape) -> np.ndarray:
        limit = np.sqrt(6 / (shape[0] + shape[1]))
        return np.random.uniform(-limit, limit, shape).astype(np.float32)

    def _load_or_save_projection(self):
        target_dim = config.ENCODER_ACTIVE_END - config.ENCODER_ACTIVE_START + 1
        if os.path.exists(self.projection_path):
            data = np.load(self.projection_path)
            self.W = data['W']
            self.b = data['b']
        else:
            # Optimized: only project to the active dims
            self.W = self._xavier_init((target_dim, config.ENCODER_DIM))
            self.b = np.zeros(target_dim, dtype=np.float32)
            os.makedirs(os.path.dirname(self.projection_path), exist_ok=True)
            np.savez(self.projection_path, W=self.W, b=self.b)

    def encode(self, text: str) -> np.ndarray:
        """
        Returns full 1024-dim edge vector (float32).
        knowledge_block[480:670] = projected fastembed output
        """
        embeddings = list(self.model.embed([text]))
        embedding = embeddings[0] # 384-dim

        projected = np.dot(self.W, embedding) + self.b

        full_knowledge = np.zeros(config.KNOWLEDGE_BLOCK_DIM, dtype=np.float32)
        full_knowledge[config.ENCODER_ACTIVE_START:config.ENCODER_ACTIVE_END+1] = projected

        full_vector = np.zeros(config.EDGE_VECTOR_DIM, dtype=np.float32)
        full_vector[:config.KNOWLEDGE_BLOCK_DIM] = full_knowledge

        return full_vector

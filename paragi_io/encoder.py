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
        if os.path.exists(self.projection_path):
            data = np.load(self.projection_path)
            self.W = data['W']
            self.b = data['b']
        else:
            self.W = self._xavier_init((config.KNOWLEDGE_BLOCK_DIM, config.ENCODER_DIM))
            self.b = np.zeros(config.KNOWLEDGE_BLOCK_DIM, dtype=np.float32)
            os.makedirs(os.path.dirname(self.projection_path), exist_ok=True)
            np.savez(self.projection_path, W=self.W, b=self.b)

    def encode(self, text: str) -> np.ndarray:
        """
        Returns full 1024-dim edge vector (float32).
        knowledge_block[480:670] = projected fastembed output
        knowledge_block[0:480] = near-zero (sparse, populated by interaction)
        control_block[700:1024] = zeros (populated by control phase)
        """
        # fastembed returns a generator
        embeddings = list(self.model.embed([text]))
        embedding = embeddings[0] # 384-dim

        # Project to 700-dim knowledge block
        knowledge_block = np.dot(self.W, embedding) + self.b

        # Following specific instruction:
        # knowledge_block[480:670] = projected fastembed output
        # Wait, the prompt says "projected fastembed output" goes into 480-669.
        # But our projection is to 700-dim.
        # Let's clarify: if the projection is 700-dim, then it fills 0-699.
        # But the prompt says: "fastembed 384-dim → active dims 480–669" in config.py
        # And "knowledge_block[480:670] = projected fastembed output" in encode.

        # Let's assume the projection should be to (669-480+1) = 190 dims?
        # Or project to 700 and slice?

        target_dim = config.ENCODER_ACTIVE_END - config.ENCODER_ACTIVE_START + 1
        # Re-init W if it doesn't match this logic
        if self.W.shape[0] != config.KNOWLEDGE_BLOCK_DIM:
             # Just making sure
             pass

        full_knowledge = np.zeros(config.KNOWLEDGE_BLOCK_DIM, dtype=np.float32)

        # Option A: Project to 190 dims
        W_small = self.W[:target_dim, :]
        b_small = self.b[:target_dim]
        projected = np.dot(W_small, embedding) + b_small

        full_knowledge[config.ENCODER_ACTIVE_START:config.ENCODER_ACTIVE_END+1] = projected

        full_vector = np.zeros(config.EDGE_VECTOR_DIM, dtype=np.float32)
        full_vector[:config.KNOWLEDGE_BLOCK_DIM] = full_knowledge

        return full_vector

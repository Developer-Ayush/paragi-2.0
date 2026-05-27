import os

EDGE_VECTOR_DIM = 1024
KNOWLEDGE_BLOCK_DIM = 700
CONTROL_BLOCK_DIM = 324

# Knowledge block regions (v12)
CONTEXTUAL_MODULATION_DIMS = (0, 279)
COGNITIVE_RETRIEVAL_DIMS = (280, 579)
FACTUAL_DIMS = (580, 639)
CAUSAL_DIMS = (640, 669)
RESERVED_DIMS = (670, 699)

# Control block regions
REGION_ACTIVATION_DIMS = (700, 799)
EXPAND_COLLAPSE_DIMS = (800, 849)
LEARNING_RATE_DIMS = (850, 899)
DECAY_RATE_DIMS = (900, 949)
CONNECTION_STRENGTH_DIMS = (950, 999)
METADATA_DIMS = (1000, 1023)

# Temporary encoder: fastembed 384-dim → active dims 480–669
ENCODER_DIM = 384
ENCODER_ACTIVE_START = 480
ENCODER_ACTIVE_END = 669

# Traversal
BEAM_WIDTH = 32
MAX_HOPS = 7
MIN_CONFIDENCE_EARLY_STOP = 0.92

# Strength / decay
STRENGTH_FLOOR = 0.001
INITIAL_STRENGTH = 0.5

# Per-region decay rates (per hour)
DECAY_RATES = {
    (0, 139): 0.0005,
    (140, 279): 0.001,
    (280, 379): 0.002,
    (380, 479): 0.004,
    (480, 579): 0.005,
    (580, 639): 0.008,
    (640, 669): 0.006,
}

# Background worker
BACKGROUND_INTERVAL_SECONDS = 30

# Storage
ROCKSDB_PATH = os.environ.get("ROCKSDB_PATH", "./data/paragi_db")
BLOOM_CAPACITY = 10_000_000
BLOOM_ERROR_RATE = 0.001

# Bootstrap
CONCEPTNET_CSV_PATH = "./data/conceptnet-assertions-5.7.0.csv"
CONCEPTNET_DOWNLOAD_URL = "https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz"

# Economy
CREDITS_PER_NEW_NODE = 10

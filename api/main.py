import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from storage.rocksdb_store import RocksDBStore
from storage.bloom import BloomFilter
from core.graph import ParagiGraph
from paragi_io.encoder import ParagiEncoder
from background.worker import BackgroundWorker
import config

from api.routes import query, graph_view, history, health

# Global state
store = None
bloom = None
graph = None
encoder = None
worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global store, bloom, graph, encoder, worker

    # Initialize components
    store = RocksDBStore(config.ROCKSDB_PATH)
    bloom = BloomFilter(config.BLOOM_CAPACITY, config.BLOOM_ERROR_RATE)
    bloom_path = "./data/bloom_filter.bin"
    if os.path.exists(bloom_path):
        bloom.load(bloom_path)

    graph = ParagiGraph(store, bloom)
    encoder = ParagiEncoder()

    # Start worker
    worker = BackgroundWorker(graph, encoder)
    worker.start()

    yield

    # Shutdown
    if worker:
        worker.stop()
    if store:
        store.close()

app = FastAPI(title="Paragi", version="1.0.0", lifespan=lifespan)

# Include routes
app.include_router(query.router)
app.include_router(graph_view.router)
app.include_router(history.router)
app.include_router(health.router)

# Mount static files - MUST BE LAST
if os.path.exists("api/static"):
    app.mount("/", StaticFiles(directory="api/static", html=True), name="static")

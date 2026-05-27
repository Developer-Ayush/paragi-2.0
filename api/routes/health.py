from fastapi import APIRouter
import time

router = APIRouter()

START_TIME = time.time()

@router.get("/health")
async def health_check():
    from api.main import graph
    return {
        "status": "ok",
        "nodes": graph.total_nodes(),
        "edges": graph.total_edges(),
        "uptime_seconds": int(time.time() - START_TIME)
    }

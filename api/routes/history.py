from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/history")
async def get_history(user_id: str, limit: int = 20):
    from api.main import graph
    # Fetch 200 records to filter by user_id
    history = graph.store.get_query_history(200)
    filtered = [h for h in history if h.get("user_id") == user_id]
    return filtered[:limit]

@router.get("/history/{query_id}/evolution")
async def get_evolution(query_id: str):
    from api.main import graph, encoder
    from paragi_io.pipeline import process_query

    # Get original record
    record = graph.store.get_query_record(query_id)
    if not record:
        return {"error": "Not found"}

    # Re-run query to see if it evolved
    new_result = process_query(record["raw_text"], graph, encoder, record["user_id"])

    return {
        "original_query": record["raw_text"],
        "asked_at": record["timestamp"],
        "frozen_answer": record["frozen_snapshot"],
        "current_answer": new_result.answer,
        "evolved": record["frozen_snapshot"] != new_result.answer
    }

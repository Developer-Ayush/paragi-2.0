from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from paragi_io.pipeline import process_query, QueryResult
import time

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    source: str
    path: List[str]
    hops: int
    credits_awarded: int
    query_id: str

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    from api.main import graph, encoder

    try:
        result = process_query(request.query, graph, encoder, request.user_id)

        # Take the best path for the response
        path_labels = []
        hops = 0
        if result.paths:
            best_path = result.paths[0]
            for nid in best_path.nodes:
                node = graph.store.get_node(nid)
                path_labels.append(node.label if node else "unknown")
            hops = best_path.hops

        return QueryResponse(
            answer=result.answer,
            confidence=result.confidence,
            source=result.source,
            path=path_labels,
            hops=hops,
            credits_awarded=0, # Simplified
            query_id=result.query_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

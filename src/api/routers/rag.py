import asyncio

from fastapi import APIRouter, Request

from src.api.schemas import RagQueryRequest, RagQueryResponse
from src.services.rag_service import run_rag_query

router = APIRouter()


@router.post("/query", response_model=RagQueryResponse)
async def rag_query(body: RagQueryRequest, request: Request):
    def _run():
        return run_rag_query(
            request.app.state.llm,
            request.app.state.vector_store,
            question=body.question,
            top_k=body.top_k,
            thread_id=body.thread_id,
            source_contains=body.source_contains,
            rewrite=body.rewrite,
            multi_query=body.multi_query,
            multi_query_n=body.multi_query_n,
            rerank=body.rerank,
            rerank_keep=body.rerank_keep,
        )

    out = await asyncio.to_thread(_run)
    return RagQueryResponse(
        retrieval_queries=list(out.get("retrieval_queries") or []),
        citations=out.get("citations") or "",
        answer=out.get("answer") or "",
    )

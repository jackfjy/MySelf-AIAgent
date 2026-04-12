"""RAG 问答（与 CLI 共用逻辑）。"""

from typing import Any

from ..llm_client import LLMClient
from ..rag.graph_builder import build_rag_graph
from ..rag.vector_store import SimpleVectorStore


def run_rag_query(
    llm: LLMClient,
    store: SimpleVectorStore,
    *,
    question: str,
    top_k: int = 4,
    thread_id: str = "default",
    source_contains: str = "",
    rewrite: bool = False,
    multi_query: bool = False,
    multi_query_n: int = 3,
    rerank: bool = False,
    rerank_keep: int = 4,
) -> dict:
    if rewrite and multi_query:
        raise ValueError("rewrite 与 multi_query 不能同时为 True")

    question = (question or "").strip()
    if not question:
        raise ValueError("question 不能为空")

    n = max(2, min(int(multi_query_n), 6))
    graph: Any = build_rag_graph(
        llm,
        store,
        top_k=int(top_k),
        multi_query_n=n,
    )
    return graph.invoke(
        {
            "question": question,
            "history": [],
            "source_contains": (source_contains or "").strip(),
            "rewrite_enabled": bool(rewrite),
            "multi_query_enabled": bool(multi_query),
            "retrieval_queries": [],
            "rerank_enabled": bool(rerank),
            "rerank_keep": int(rerank_keep),
            "candidates": [],
            "retrieved_context": "",
            "reranked_context": "",
            "citations": "",
            "answer": "",
        },
        config={"configurable": {"thread_id": (thread_id or "default").strip() or "default"}},
    )

from ..llm_client import LLMInput, LLMClient
from .prompts import RAG_ANSWER_PROMPT
from .vector_store import SimpleVectorStore


def retrieve_node(state, store: SimpleVectorStore, top_k: int) -> dict:
    q = state["question"]
    results = store.similarity_search(q, k=top_k)
    if not results:
        return {
            "retrieved_context": "（知识库为空或尚未入库，请先运行 python -m src.rag.ingest）",
            "citations": "",
        }
    parts: list[str] = []
    cites: list[str] = []
    for chunk, score in results:
        text = chunk["text"]
        meta = chunk.get("metadata") or {}
        src = meta.get("source", "unknown")
        cid = chunk["id"]
        parts.append(f"[片段 id={cid} score={score:.3f} source={src}]\n{text}")
        cites.append(f"- id={cid} score={score:.3f} source={src}")
    return {
        "retrieved_context": "\n\n".join(parts),
        "citations": "\n".join(cites),
    }


def answer_node(state, llm: LLMClient) -> dict:
    prompt = RAG_ANSWER_PROMPT.format(
        context=state["retrieved_context"],
        question=state["question"],
    )
    out = llm.invoke(LLMInput(prompt=prompt))
    return {"answer": out.text}

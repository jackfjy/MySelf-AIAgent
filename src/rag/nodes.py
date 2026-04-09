import json
import re

from ..llm_client import LLMInput, LLMClient
from .prompts import (
    RAG_ANSWER_PROMPT,
    RAG_MULTI_QUERY_PROMPT,
    RAG_QUERY_REWRITE_PROMPT,
    RAG_RERANK_PROMPT,
)
from .vector_store import SimpleVectorStore


def _merge_vec_bm25(
    vec_results: list[tuple[dict, float]],
    bm25_results: list[tuple[dict, float]],
) -> list[tuple[dict, float, str]]:
    merged: list[tuple[dict, float, str]] = []
    seen: set[int] = set()
    for chunk, score in vec_results:
        cid = int(chunk["id"])
        if cid not in seen:
            seen.add(cid)
            merged.append((chunk, score, "vec"))
    for chunk, score in bm25_results:
        cid = int(chunk["id"])
        if cid not in seen:
            seen.add(cid)
            merged.append((chunk, score, "bm25"))
    return merged


def _merge_cross_query(groups: list[list[tuple[dict, float, str]]]) -> list[tuple[dict, float, str]]:
    """多路检索合并：同一 chunk id 保留分数更高的那条。"""
    best: dict[int, tuple[dict, float, str]] = {}
    for group in groups:
        for chunk, score, src_type in group:
            cid = int(chunk["id"])
            if cid not in best or score > best[cid][1]:
                best[cid] = (chunk, score, src_type)
    return sorted(best.values(), key=lambda x: -x[1])


def rewrite_query_node(state, llm: LLMClient, multi_n: int = 3) -> dict:
    """生成 retrieval_queries；与 --multi-query / --rewrite 配合。"""
    question = (state.get("question") or "").strip()
    history = state.get("history") or []
    history_tail = history[-6:]
    history_text = "\n".join(
        [f"Q{i+1}: {t.get('question', '')}\nA{i+1}: {t.get('answer', '')}" for i, t in enumerate(history_tail)]
    ).strip()
    if not history_text:
        history_text = "（无）"

    multi = bool(state.get("multi_query_enabled"))
    rewrite = bool(state.get("rewrite_enabled"))

    if multi:
        n = max(2, min(int(multi_n), 6))
        prompt = RAG_MULTI_QUERY_PROMPT.format(history=history_text, question=question, n=n)
        raw = llm.invoke(LLMInput(prompt=prompt)).text.strip()
        queries: list[str] = []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                queries = [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            queries = []
        if len(queries) < 2:
            queries = [question, question]
        queries = queries[:n]
        return {"retrieval_queries": queries}

    if rewrite:
        prompt = RAG_QUERY_REWRITE_PROMPT.format(history=history_text, question=question)
        raw = llm.invoke(LLMInput(prompt=prompt)).text.strip()
        q1 = raw.splitlines()[0].strip().strip('"').strip("'")
        if not q1:
            q1 = question
        return {"retrieval_queries": [q1]}

    return {"retrieval_queries": [question]}


def retrieve_node(state, store: SimpleVectorStore, top_k: int) -> dict:
    source_contains = (state.get("source_contains") or "").strip() or None
    queries = state.get("retrieval_queries") or []
    if not queries:
        queries = [state["question"].strip()]

    groups: list[list[tuple[dict, float, str]]] = []
    for q in queries:
        vec_results = store.similarity_search(
            q,
            k=top_k,
            source_contains=source_contains,
        )
        bm25_results = store.bm25_search(
            q,
            k=top_k,
            source_contains=source_contains,
        )
        groups.append(_merge_vec_bm25(vec_results, bm25_results))

    if not groups:
        results = []
    elif len(groups) == 1:
        results = sorted(groups[0], key=lambda x: -x[1])
    else:
        results = _merge_cross_query(groups)
    if not results:
        return {
            "retrieved_context": "（知识库为空或尚未入库，请先运行 python -m src.rag.ingest）",
            "citations": "",
            "candidates": [],
            "reranked_context": "",
        }
    parts: list[str] = []
    cites: list[str] = []
    candidates: list[dict[str, str]] = []
    for chunk, score, src_type in results:
        text = chunk["text"]
        meta = chunk.get("metadata") or {}
        src = meta.get("source", "unknown")
        cid = chunk["id"]
        parts.append(f"[片段 id={cid} type={src_type} score={score:.3f} source={src}]\n{text}")
        cites.append(f"- id={cid} type={src_type} score={score:.3f} source={src}")
        candidates.append(
            {
                "id": str(cid),
                "type": src_type,
                "score": f"{score:.6f}",
                "source": str(src),
                "text": text,
            }
        )
    return {
        "retrieved_context": "\n\n".join(parts),
        "candidates": candidates,
        "reranked_context": "",
        "citations": "\n".join(cites),
    }


def rerank_node(state, llm: LLMClient) -> dict:
    if not state.get("rerank_enabled"):
        return {"reranked_context": state.get("retrieved_context", "")}

    keep = int(state.get("rerank_keep") or 4)
    keep = max(1, min(keep, 10))
    candidates = state.get("candidates") or []
    if not candidates:
        return {"reranked_context": state.get("retrieved_context", "")}

    # 控制 rerank prompt 长度：只给前 N 个候选
    top_candidates = candidates[: max(keep * 3, keep)]
    c_text = "\n\n".join(
        [
            f"[id={c['id']} type={c.get('type')} score={c.get('score')} source={c.get('source')}]\n{c.get('text','')}"
            for c in top_candidates
        ]
    )
    prompt = RAG_RERANK_PROMPT.format(
        question=state["question"],
        candidates=c_text,
        keep=keep,
    )
    raw = llm.invoke(LLMInput(prompt=prompt)).text.strip()

    # 尽量稳健地解析：优先 JSON；失败则提取数字
    ids: list[int] = []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            ids = [int(x) for x in parsed if str(x).strip().isdigit()]
    except Exception:
        ids = [int(x) for x in re.findall(r"\b\d+\b", raw)]

    if not ids:
        ids = [int(top_candidates[0]["id"])]
    ids = ids[:keep]
    id_set = {str(i) for i in ids}

    selected = [c for c in top_candidates if c.get("id") in id_set]
    # 如果模型选的 id 不在 top_candidates（或被过滤掉），则回退补齐
    if not selected:
        selected = top_candidates[:keep]

    reranked_parts = []
    for c in selected:
        reranked_parts.append(
            f"[片段 id={c.get('id')} type={c.get('type')} score={c.get('score')} source={c.get('source')}]\n{c.get('text','')}"
        )
    return {"reranked_context": "\n\n".join(reranked_parts)}


def answer_node(state, llm: LLMClient) -> dict:
    history = state.get("history") or []
    # 只取最近几轮，避免 prompt 无限增长
    history_tail = history[-6:]
    history_text = "\n".join(
        [f"Q{i+1}: {t.get('question','')}\nA{i+1}: {t.get('answer','')}" for i, t in enumerate(history_tail)]
    ).strip()
    if not history_text:
        history_text = "（无）"

    prompt = RAG_ANSWER_PROMPT.format(
        history=history_text,
        context=(state.get("reranked_context") or state.get("retrieved_context") or ""),
        question=state["question"],
    )
    out = llm.invoke(LLMInput(prompt=prompt))
    new_turn = {"question": state["question"], "answer": out.text}
    return {"answer": out.text, "history": history + [new_turn]}

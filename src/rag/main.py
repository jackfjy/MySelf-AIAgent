"""
知识库问答入口（RAG 图）。

在项目根目录执行：
  python -m src.rag.main --question "你的问题"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import get_settings
from src.llm_client import LLMClient
from src.rag.embeddings import build_openai_embeddings
from src.rag.vector_store import SimpleVectorStore
from src.services.rag_service import run_rag_query


def main() -> None:
    p = argparse.ArgumentParser(description="知识库问答（RAG）")
    p.add_argument("--question", "-q", required=True, help="用户问题")
    p.add_argument("--top-k", type=int, default=4, help="检索片段数")
    p.add_argument("--thread-id", type=str, default="default", help="会话 id（相同 id 共享记忆）")
    p.add_argument(
        "--source-contains",
        type=str,
        default="",
        help="仅检索 source 含该子串的文档片段（例如 sample.md / hr/ / handbook）",
    )
    p.add_argument("--rerank", action="store_true", help="开启 LLM rerank（会额外调用一次模型）")
    p.add_argument("--rerank-keep", type=int, default=4, help="rerank 最终保留片段数")
    qg = p.add_mutually_exclusive_group()
    qg.add_argument(
        "--rewrite",
        action="store_true",
        help="查询改写：用 LLM 生成一条更适合检索的 query（额外 1 次模型调用）",
    )
    qg.add_argument(
        "--multi-query",
        action="store_true",
        help="多查询扩展：用 LLM 生成多条检索 query 分别检索后合并（额外 1 次模型调用）",
    )
    p.add_argument(
        "--multi-query-n",
        type=int,
        default=3,
        help="与 --multi-query 配合：生成几条检索 query（2-6）",
    )
    args = p.parse_args()

    settings = get_settings()
    llm = LLMClient(
        provider=settings.provider,
        model_name=settings.model_name,
        openai_api_key=settings.openai_api_key,
        openai_base_url=settings.openai_base_url,
        openai_http_proxy=settings.openai_http_proxy,
        deepseek_api_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
    )
    emb = build_openai_embeddings()
    kb_dir = os.getenv("KB_DATA_DIR", "data/kb").strip()
    store = SimpleVectorStore(emb, _ROOT / kb_dir)
    out = run_rag_query(
        llm,
        store,
        question=args.question,
        top_k=args.top_k,
        thread_id=args.thread_id,
        source_contains=args.source_contains,
        rewrite=bool(args.rewrite),
        multi_query=bool(args.multi_query),
        multi_query_n=int(args.multi_query_n),
        rerank=bool(args.rerank),
        rerank_keep=int(args.rerank_keep),
    )
    rq = out.get("retrieval_queries") or []
    if rq:
        print("--- 检索 query ---")
        for i, q in enumerate(rq, start=1):
            print(f"{i}. {q}")
    print("--- 引用 ---")
    print(out.get("citations") or "(无)")
    print("--- 回答 ---")
    print(out["answer"])


if __name__ == "__main__":
    main()

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
from src.rag.graph_builder import build_rag_graph
from src.rag.vector_store import SimpleVectorStore


def main() -> None:
    p = argparse.ArgumentParser(description="知识库问答（RAG）")
    p.add_argument("--question", "-q", required=True, help="用户问题")
    p.add_argument("--top-k", type=int, default=4, help="检索片段数")
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
    graph = build_rag_graph(llm, store, top_k=args.top_k)
    out = graph.invoke(
        {
            "question": args.question,
            "retrieved_context": "",
            "citations": "",
            "answer": "",
        }
    )
    print("--- 引用 ---")
    print(out.get("citations") or "(无)")
    print("--- 回答 ---")
    print(out["answer"])


if __name__ == "__main__":
    main()

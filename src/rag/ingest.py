"""
将本地文本/Markdown 切分后写入向量库。

用法（在项目根目录）：
  python -m src.rag.ingest --path data/docs
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from ..config import get_settings
from .embeddings import build_openai_embeddings
from .vector_store import SimpleVectorStore


def _chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> None:
    parser = argparse.ArgumentParser(description="入库：扫描目录下的 .md .txt")
    parser.add_argument(
        "--path",
        type=str,
        default="data/docs",
        help="待入库目录（相对项目根）",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=800,
        help="每段最大字符数",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="入库前清空已有索引",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    docs_dir = (root / args.path).resolve()
    if not docs_dir.is_dir():
        raise SystemExit(f"目录不存在: {docs_dir}")

    get_settings()
    kb_dir = Path(os.getenv("KB_DATA_DIR", "data/kb"))
    persist = (root / kb_dir).resolve()

    emb = build_openai_embeddings()
    store = SimpleVectorStore(emb, persist)

    if args.clear:
        store.clear()

    exts = {".md", ".txt", ".markdown"}
    files = [p for p in docs_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts]
    if not files:
        raise SystemExit(f"未找到 .md/.txt 文件: {docs_dir}")

    total = 0
    for fp in sorted(files):
        rel = str(fp.relative_to(docs_dir))
        raw = _read_file(fp)
        pieces = _chunk_text(raw, max_chars=args.max_chars)
        texts = pieces
        metas = [{"source": rel, "path": str(fp)} for _ in texts]
        store.add_texts(texts, metas)
        total += len(texts)
        print(f"OK {rel} -> {len(texts)} chunks")

    print(f"完成：共 {total} 条片段，索引目录 {persist}，当前库大小 {store.size}")


if __name__ == "__main__":
    main()

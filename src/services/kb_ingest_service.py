"""知识库入库（目录扫描或上传文本），与 CLI / HTTP 共用。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..rag.document_extract import allowed_suffixes
from ..rag.ingest_utils import chunk_text
from ..rag.vector_store import SimpleVectorStore


ALLOWED_UPLOAD_SUFFIX = allowed_suffixes()


def ingest_uploaded_texts(
    store: SimpleVectorStore,
    files: list[tuple[str, str]],
    *,
    max_chars: int = 800,
    clear_before: bool = False,
    metas_extra: list[dict[str, Any]] | None = None,
) -> dict:
    """
    将多份「文件名 + 文本」写入向量库。

    files: (logical_source_name, utf8_text)，如 ("手册.md", "...")
    metas_extra: 与 files 等长，每条合并进每个 chunk 的 metadata（如 upload_id）。
    """
    if clear_before:
        store.clear()

    if metas_extra is not None and len(metas_extra) != len(files):
        raise ValueError("metas_extra 长度须与 files 一致")

    total_chunks = 0
    details: list[dict] = []

    for i, (source_name, raw) in enumerate(files):
        source_name = (source_name or "unknown").strip().replace("\\", "/")
        suf = Path(source_name).suffix.lower()
        if suf not in ALLOWED_UPLOAD_SUFFIX:
            details.append({"source": source_name, "chunks": 0, "skipped": True})
            continue
        pieces = chunk_text(raw, max_chars=max_chars)
        if not pieces:
            details.append({"source": source_name, "chunks": 0, "skipped": True})
            continue
        extra: dict[str, Any] = {}
        if metas_extra and i < len(metas_extra) and metas_extra[i]:
            extra = {k: v for k, v in metas_extra[i].items() if v is not None}
        metas = [
            {"source": f"upload/{source_name}", "path": f"upload:{source_name}", **extra}
            for _ in pieces
        ]
        store.add_texts(pieces, metas)
        n = len(pieces)
        total_chunks += n
        details.append({"source": source_name, "chunks": n, "skipped": False})

    return {
        "chunks_added": total_chunks,
        "files_processed": len([d for d in details if not d.get("skipped")]),
        "store_size": store.size,
        "details": details,
    }

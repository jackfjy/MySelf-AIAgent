"""知识库入库（目录扫描或上传文本），与 CLI / HTTP 共用。"""

from pathlib import Path

from ..rag.ingest_utils import chunk_text
from ..rag.vector_store import SimpleVectorStore


ALLOWED_UPLOAD_SUFFIX = {".md", ".txt", ".markdown"}


def ingest_uploaded_texts(
    store: SimpleVectorStore,
    files: list[tuple[str, str]],
    *,
    max_chars: int = 800,
    clear_before: bool = False,
) -> dict:
    """
    将多份「文件名 + 文本」写入向量库。

    files: (logical_source_name, utf8_text)，如 ("手册.md", "...")
    """
    if clear_before:
        store.clear()

    total_chunks = 0
    details: list[dict] = []

    for source_name, raw in files:
        source_name = (source_name or "unknown").strip().replace("\\", "/")
        suf = Path(source_name).suffix.lower()
        if suf and suf not in ALLOWED_UPLOAD_SUFFIX:
            continue
        pieces = chunk_text(raw, max_chars=max_chars)
        if not pieces:
            details.append({"source": source_name, "chunks": 0, "skipped": True})
            continue
        metas = [{"source": f"upload/{source_name}", "path": f"upload:{source_name}"} for _ in pieces]
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

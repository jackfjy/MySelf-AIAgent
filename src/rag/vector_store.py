from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from langchain_openai import OpenAIEmbeddings


class SimpleVectorStore:
    """
    MVP：本地文件持久化（chunks.jsonl + embeddings.npy）+ 余弦相似度检索。
    后续可替换为 pgvector / Milvus 等。
    """

    def __init__(self, embeddings: OpenAIEmbeddings, persist_dir: Path) -> None:
        self.embeddings = embeddings
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._chunks_path = self.persist_dir / "chunks.jsonl"
        self._emb_path = self.persist_dir / "embeddings.npy"
        self._chunks: list[dict[str, Any]] = []
        self._emb: np.ndarray | None = None
        self._load()

    def _load(self) -> None:
        if not self._chunks_path.exists() or not self._emb_path.exists():
            return
        self._chunks = []
        with open(self._chunks_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._chunks.append(json.loads(line))
        self._emb = np.load(self._emb_path)

    def _save(self) -> None:
        with open(self._chunks_path, "w", encoding="utf-8") as f:
            for c in self._chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        if self._emb is not None:
            np.save(self._emb_path, self._emb)

    @property
    def size(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        self._chunks = []
        self._emb = None
        for p in (self._chunks_path, self._emb_path):
            if p.exists():
                p.unlink()

    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        if not texts:
            return
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if len(metadatas) != len(texts):
            raise ValueError("metadatas 长度须与 texts 一致")

        vecs = self.embeddings.embed_documents(texts)
        arr = np.asarray(vecs, dtype=np.float32)
        start_id = len(self._chunks)
        for i, t in enumerate(texts):
            self._chunks.append(
                {
                    "id": start_id + i,
                    "text": t,
                    "metadata": metadatas[i],
                }
            )
        if self._emb is None:
            self._emb = arr
        else:
            self._emb = np.vstack([self._emb, arr])
        self._save()

    def similarity_search(
        self, query: str, k: int = 4
    ) -> list[tuple[dict[str, Any], float]]:
        if not self._chunks or self._emb is None:
            return []
        k = min(k, len(self._chunks))
        q_vec = np.asarray(self.embeddings.embed_query(query), dtype=np.float32)
        emb = self._emb
        emb_norm = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10)
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-10)
        scores = emb_norm @ q_norm
        top_idx = np.argsort(-scores)[:k]
        return [(self._chunks[int(i)], float(scores[i])) for i in top_idx]

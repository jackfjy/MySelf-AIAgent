"""文本切块（供 CLI 入库与 HTTP 上传共用）。"""


def chunk_text(text: str, max_chars: int = 800, overlap: int = 100) -> list[str]:
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

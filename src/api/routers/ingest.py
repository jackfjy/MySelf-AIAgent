import asyncio
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from src.services.kb_ingest_service import ALLOWED_UPLOAD_SUFFIX, ingest_uploaded_texts

router = APIRouter()

# 单文件约 5MB，最多 30 个文件（可按需调大）
MAX_FILES = 30
MAX_BYTES_PER_FILE = 5 * 1024 * 1024


@router.post("/ingest")
async def rag_ingest(
    request: Request,
    files: list[UploadFile] = File(...),
    clear: bool = Form(False),
    max_chars: int = Form(800),
):
    if not files:
        raise HTTPException(400, "请至少上传一个文件")
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"单次最多上传 {MAX_FILES} 个文件")

    store = request.app.state.vector_store

    async def _read_one(uf: UploadFile) -> tuple[str, str]:
        name = uf.filename or "unnamed.txt"
        suf = Path(name).suffix.lower()
        if suf not in ALLOWED_UPLOAD_SUFFIX:
            raise HTTPException(
                400,
                f"不支持的文件类型: {name}（仅允许 {', '.join(sorted(ALLOWED_UPLOAD_SUFFIX))}）",
            )
        data = await uf.read()
        if len(data) > MAX_BYTES_PER_FILE:
            raise HTTPException(400, f"文件过大: {name}（单文件上限 {MAX_BYTES_PER_FILE} 字节）")
        text = data.decode("utf-8", errors="ignore")
        return name, text

    pairs: list[tuple[str, str]] = []
    for uf in files:
        pairs.append(await _read_one(uf))

    def _run():
        return ingest_uploaded_texts(
            store,
            pairs,
            max_chars=max(200, min(int(max_chars), 4000)),
            clear_before=clear,
        )

    result = await asyncio.to_thread(_run)
    return result

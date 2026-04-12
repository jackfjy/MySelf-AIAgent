import asyncio
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from src.api.schemas import RagReingestRequest
from src.rag.document_extract import DocumentExtractError, allowed_suffixes, extract_plain_text
from src.services.kb_ingest_service import ingest_uploaded_texts
from src.services.upload_history import UploadHistory

router = APIRouter()

ALLOWED_UPLOAD_SUFFIX = allowed_suffixes()

# 二进制文档可能较大，单文件上限略高于纯文本
MAX_FILES = 30
MAX_BYTES_PER_FILE = 12 * 1024 * 1024


@router.get("/uploads")
def list_uploads(request: Request):
    """列出历史上传并保存在磁盘上的原始文件（用于再次入库）。"""
    hist: UploadHistory = request.app.state.upload_history
    items = [r.to_json() for r in hist.list_records()]
    return {"items": items, "count": len(items)}


@router.post("/reingest")
async def rag_reingest(request: Request, body: RagReingestRequest):
    """从已保存的原始文件再次解析并写入向量库（无需重新上传）。"""
    hist: UploadHistory = request.app.state.upload_history
    store = request.app.state.vector_store

    prepared: list[tuple[str, str, dict]] = []
    for uid in dict.fromkeys(body.ids):
        rec = hist.get_record(uid)
        if not rec:
            raise HTTPException(404, f"找不到上传记录: {uid}")
        path = hist.path_for(rec)
        if not path.is_file():
            raise HTTPException(400, f"原始文件已丢失: {rec.original_name}")
        data = path.read_bytes()
        try:
            text = extract_plain_text(rec.original_name, data)
        except DocumentExtractError as e:
            raise HTTPException(400, str(e)) from e
        if not (text or "").strip():
            raise HTTPException(400, f"未能解析出文本: {rec.original_name}")
        prepared.append((rec.original_name, text, {"upload_id": rec.id}))

    def _run():
        return ingest_uploaded_texts(
            store,
            [(n, t) for n, t, _ in prepared],
            max_chars=max(200, min(int(body.max_chars), 4000)),
            clear_before=body.clear,
            metas_extra=[m for _, _, m in prepared],
        )

    return await asyncio.to_thread(_run)


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
    hist: UploadHistory = request.app.state.upload_history

    raw_list: list[tuple[str, bytes]] = []

    async def _read_one(uf: UploadFile) -> None:
        name = uf.filename or "unnamed.txt"
        suf = Path(name).suffix.lower()
        if suf not in ALLOWED_UPLOAD_SUFFIX:
            raise HTTPException(
                400,
                f"不支持的文件类型: {name}（允许 {', '.join(sorted(ALLOWED_UPLOAD_SUFFIX))}）",
            )
        data = await uf.read()
        if len(data) > MAX_BYTES_PER_FILE:
            raise HTTPException(400, f"文件过大: {name}（单文件上限 {MAX_BYTES_PER_FILE} 字节）")
        raw_list.append((name, data))

    for uf in files:
        await _read_one(uf)

    pairs: list[tuple[str, str]] = []
    metas_extra: list[dict] = []
    for name, data in raw_list:
        try:
            text = extract_plain_text(name, data)
        except DocumentExtractError as e:
            raise HTTPException(400, str(e)) from e
        if not (text or "").strip():
            raise HTTPException(400, f"未解析到文本内容: {name}")
        rec = hist.save_original(name, data)
        pairs.append((name, text))
        metas_extra.append({"upload_id": rec.id})

    def _run():
        return ingest_uploaded_texts(
            store,
            pairs,
            max_chars=max(200, min(int(max_chars), 4000)),
            clear_before=clear,
            metas_extra=metas_extra,
        )

    result = await asyncio.to_thread(_run)
    return result

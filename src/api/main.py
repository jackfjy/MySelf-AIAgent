"""
FastAPI 应用入口。

启动（项目根目录）：
  uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.graph_builder import build_content_graph
from src.llm_client import LLMClient
from src.rag.embeddings import build_openai_embeddings
from src.rag.vector_store import SimpleVectorStore
from src.services.upload_history import UploadHistory

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    app.state.llm = llm
    app.state.content_graph = build_content_graph(llm)
    app.state.embeddings = build_openai_embeddings()
    kb_dir = os.getenv("KB_DATA_DIR", "data/kb").strip()
    persist = _PROJECT_ROOT / kb_dir
    app.state.vector_store = SimpleVectorStore(app.state.embeddings, persist)
    app.state.upload_history = UploadHistory(persist)
    yield


app = FastAPI(
    title="LangGraph Demo API",
    version="0.1.0",
    lifespan=lifespan,
)

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.api.routers.content import router as content_router
from src.api.routers.ingest import router as ingest_router
from src.api.routers.rag import router as rag_router

app.include_router(content_router, prefix="/api/v1/content")
app.include_router(rag_router, prefix="/api/v1/rag")
app.include_router(ingest_router, prefix="/api/v1/rag")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "docs": "/docs",
        "health": "/health",
        "content_generate": "POST /api/v1/content/generate",
        "rag_query": "POST /api/v1/rag/query",
        "rag_ingest": "POST /api/v1/rag/ingest",
        "rag_uploads": "GET /api/v1/rag/uploads",
        "rag_reingest": "POST /api/v1/rag/reingest",
    }

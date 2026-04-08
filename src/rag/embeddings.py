import os

import httpx
from langchain_openai import OpenAIEmbeddings

from ..config import get_settings
from ..http_utils import normalize_http_proxy_url


def build_openai_embeddings() -> OpenAIEmbeddings:
    """
    构建与 Chat 相同鉴权/代理/兼容 Base 的 Embedding 客户端。
    可用环境变量覆盖：
    - EMBEDDING_OPENAI_API_KEY / EMBEDDING_OPENAI_BASE_URL（不填则沿用 OPENAI_*）
    - OPENAI_EMBEDDING_MODEL（默认 text-embedding-3-small）
    """
    s = get_settings()
    api_key = os.getenv("EMBEDDING_OPENAI_API_KEY") or s.openai_api_key
    if not api_key:
        raise ValueError(
            "RAG 需要向量模型：请在 .env 配置 OPENAI_API_KEY，或单独设置 EMBEDDING_OPENAI_API_KEY"
        )
    base_url = os.getenv("EMBEDDING_OPENAI_BASE_URL") or s.openai_base_url
    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()

    http_client: httpx.Client | None = None
    if s.openai_http_proxy:
        http_client = httpx.Client(
            proxy=normalize_http_proxy_url(s.openai_http_proxy),
            timeout=httpx.Timeout(120.0),
        )

    kwargs: dict = {
        "model": model,
        "api_key": api_key,
    }
    if base_url:
        kwargs["openai_api_base"] = base_url
    if http_client is not None:
        kwargs["http_client"] = http_client

    return OpenAIEmbeddings(**kwargs)

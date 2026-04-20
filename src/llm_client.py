from dataclasses import dataclass

import httpx
from typing import List, Dict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI


def _normalize_http_proxy_url(url: str) -> str:
    """
    本地 HTTP 代理应使用 http://127.0.0.1:端口；误写 https://127.0.0.1 时部分环境会 CONNECT 失败。
    """
    u = url.strip()
    if u.startswith("https://127.0.0.1") or u.startswith("https://localhost"):
        return "http://" + u[len("https://") :]
    return u


@dataclass(frozen=True)
class LLMInput:
    prompt: str


@dataclass(frozen=True)
class LLMOutput:
    text: str

# 用于输出 fact_checker 和 reviewer 的 JSON 格式的 LLM 响应，包含 status, issues, revised_text
@dataclass(frozen=True)
class LLMOutputJSON(LLMOutput):
    status: str
    issues: List[Dict[str, str]]
    revised_text: str

class LLMClient:
    """
    统一封装：后续节点只关心 invoke(prompt)。
    底层使用 LangChain 的 ChatOpenAI，Deepseek 通过 OpenAI-compatible API base_url 复用。
    """

    def __init__(
        self,
        provider: str,
        model_name: str,
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
        openai_http_proxy: str | None = None,
        deepseek_api_key: str | None = None,
        deepseek_base_url: str | None = None,
        temperature: float = 0.7,
    ):
        self.provider = provider.lower().strip()
        self.model_name = model_name

        if self.provider == "openai":
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when PROVIDER=openai")
            api_key = openai_api_key
            # 官方或第三方兼容 API 的 base；与「本地翻墙代理」OPENAI_HTTP_PROXY 是两回事
            base_url = openai_base_url.strip() if openai_base_url else None
        elif self.provider == "deepseek":
            if not deepseek_api_key:
                raise ValueError("DEEPSEEK_API_KEY is required when PROVIDER=deepseek")
            if not deepseek_base_url:
                raise ValueError("DEEPSEEK_BASE_URL is required when PROVIDER=deepseek")
            api_key = deepseek_api_key
            base_url = deepseek_base_url
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        http_client: httpx.Client | None = None
        if self.provider == "openai" and openai_http_proxy:
            proxy_url = _normalize_http_proxy_url(openai_http_proxy)
            http_client = httpx.Client(
                proxy=proxy_url,
                timeout=httpx.Timeout(120.0),
            )

        llm_kwargs: dict = {
            "model": self.model_name,
            "api_key": api_key,
            "base_url": base_url,
            "temperature": temperature,
        }
        if http_client is not None:
            llm_kwargs["http_client"] = http_client

        self._llm = ChatOpenAI(**llm_kwargs)

    def invoke(self, llm_input: LLMInput) -> LLMOutput:
        resp = self._llm.invoke([HumanMessage(content=llm_input.prompt)])
        return LLMOutput(text=resp.content or "")


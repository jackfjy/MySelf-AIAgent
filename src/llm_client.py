from dataclasses import dataclass

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from .http_utils import normalize_http_proxy_url


@dataclass(frozen=True)
class LLMInput:
    prompt: str


@dataclass(frozen=True)
class LLMOutput:
    text: str


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
            proxy_url = normalize_http_proxy_url(openai_http_proxy)
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


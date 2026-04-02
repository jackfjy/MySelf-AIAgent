from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

# 始终从「项目根目录」加载 .env，避免从别的 cwd 启动时读不到变量
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    provider: str
    model_name: str
    openai_api_key: str | None
    # 第三方/自建 OpenAI 兼容接口的 base（如 https://xxx/v1），不是「本地翻墙代理」
    openai_base_url: str | None
    # 本地 HTTP 代理（Clash HTTP 端口等），形如 http://127.0.0.1:7890；勿填 API 网址
    openai_http_proxy: str | None
    deepseek_api_key: str | None
    deepseek_base_url: str | None


def get_settings() -> Settings:
    provider = os.getenv("PROVIDER", "openai").lower().strip()
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()
    proxy = os.getenv("OPENAI_HTTP_PROXY", "").strip() or None
    base = os.getenv("OPENAI_BASE_URL", "").strip() or None

    return Settings(
        provider=provider,
        model_name=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_base_url=base,
        openai_http_proxy=proxy,
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL"),
    )


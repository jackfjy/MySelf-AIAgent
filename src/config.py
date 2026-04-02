from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    provider: str
    model_name: str
    openai_api_key: str | None
    # 仅当 PROVIDER=openai 时使用，例如 http://127.0.0.1:7890（见 OPENAI_HTTP_PROXY）
    openai_http_proxy: str | None
    deepseek_api_key: str | None
    deepseek_base_url: str | None


def get_settings() -> Settings:
    provider = os.getenv("PROVIDER", "openai").lower().strip()
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini").strip()
    proxy = os.getenv("OPENAI_HTTP_PROXY", "").strip() or None

    return Settings(
        provider=provider,
        model_name=model_name,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_http_proxy=proxy,
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL"),
    )


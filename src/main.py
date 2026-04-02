import argparse
import sys
from pathlib import Path

# 支持两种方式启动：
# 1) 推荐：在项目根目录执行  python -m src.main
# 2) 直接脚本：python src/main.py 或 IDE 里运行本文件（需把项目根加入 path）
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.config import get_settings
from src.graph_builder import build_content_graph
from src.llm_client import LLMClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="AI 在教育中的应用")
    args = parser.parse_args()

    settings = get_settings()
    llm = LLMClient(
        provider=settings.provider,
        model_name=settings.model_name,
        openai_api_key=settings.openai_api_key,
        openai_http_proxy=settings.openai_http_proxy,
        deepseek_api_key=settings.deepseek_api_key,
        deepseek_base_url=settings.deepseek_base_url,
    )

    graph = build_content_graph(llm)
    result = graph.invoke(
        {
            "topic": args.topic,
            "research_summary": "",
            "draft": "",
            "final_text": "",
        }
    )
    print(result["final_text"])


if __name__ == "__main__":
    main()


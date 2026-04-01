import argparse

from .config import get_settings
from .graph_builder import build_content_graph
from .llm_client import LLMClient


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, default="AI 在教育中的应用")
    args = parser.parse_args()

    settings = get_settings()
    llm = LLMClient(
        provider=settings.provider,
        model_name=settings.model_name,
        openai_api_key=settings.openai_api_key,
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


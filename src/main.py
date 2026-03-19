import argparse

from .config import get_settings
from .llm_client import LLMClient, LLMInput
from .agent_nodes import research_node


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

    # Step 2: 先只跑 Research 单节点
    research_summary = research_node(args.topic, llm)
    print(research_summary)


if __name__ == "__main__":
    main()


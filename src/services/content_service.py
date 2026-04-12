"""内容生成：Research → Writer → Editor（与 CLI 共用逻辑）。"""

from typing import Any

from ..llm_client import LLMClient


def run_content_generation(llm: LLMClient, graph: Any, topic: str) -> dict:
    """
    执行内容生成图，返回完整 state（含 research_summary / draft / final_text）。
    """
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("topic 不能为空")

    return graph.invoke(
        {
            "topic": topic,
            "research_summary": "",
            "draft": "",
            "final_text": "",
        }
    )

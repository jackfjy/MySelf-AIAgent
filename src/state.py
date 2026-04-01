from typing import TypedDict


class AgentState(TypedDict):
    """LangGraph 在节点间传递的共享状态。"""

    topic: str
    research_summary: str
    draft: str
    final_text: str

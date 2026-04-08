from typing import TypedDict


class RagState(TypedDict):
    """知识库问答在 LangGraph 中传递的状态。"""

    question: str
    retrieved_context: str
    citations: str
    answer: str

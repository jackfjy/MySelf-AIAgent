from typing import TypedDict


class RagState(TypedDict):
    """知识库问答在 LangGraph 中传递的状态。"""

    question: str
    # 简单会话记忆：按轮次累积的问答（由 checkpointer 持久化）
    history: list[dict[str, str]]
    # 元数据过滤（可选）：用于限制检索范围
    # 目前支持：source_contains（只检索 source 含某子串的片段）
    source_contains: str
    # 查询改写（可选）：由 rewrite_query 节点写入，retrieve 使用
    rewrite_enabled: bool
    multi_query_enabled: bool
    retrieval_queries: list[str]
    # rerank 开关与参数
    rerank_enabled: bool
    rerank_keep: int
    # 检索候选（结构化，供 rerank 使用）
    candidates: list[dict[str, str]]
    retrieved_context: str
    reranked_context: str
    citations: str
    answer: str

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from ..llm_client import LLMClient
from .nodes import answer_node, rerank_node, retrieve_node, rewrite_query_node
from .state import RagState
from .vector_store import SimpleVectorStore


def build_rag_graph(
    llm: LLMClient,
    store: SimpleVectorStore,
    top_k: int = 4,
    *,
    multi_query_n: int = 3,
    checkpointer: MemorySaver | None = None,
):
    def rewrite_query(state: RagState):
        return rewrite_query_node(state, llm, multi_n=multi_query_n)

    def retrieve(state: RagState):
        return retrieve_node(state, store, top_k)

    def rerank(state: RagState):
        return rerank_node(state, llm)

    def generate_answer(state: RagState):
        return answer_node(state, llm)

    g = StateGraph(RagState)
    g.add_node("rewrite_query", rewrite_query)
    g.add_node("retrieve", retrieve)
    g.add_node("rerank", rerank)
    # 节点名不能与 state key 重名（RagState 里有 answer 字段）
    g.add_node("generate_answer", generate_answer)
    g.add_edge(START, "rewrite_query")
    g.add_edge("rewrite_query", "retrieve")
    g.add_edge("retrieve", "rerank")
    g.add_edge("rerank", "generate_answer")
    g.add_edge("generate_answer", END)
    if checkpointer is None:
        checkpointer = MemorySaver()
    return g.compile(checkpointer=checkpointer)

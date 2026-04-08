from langgraph.graph import END, START, StateGraph

from ..llm_client import LLMClient
from .nodes import answer_node, retrieve_node
from .state import RagState
from .vector_store import SimpleVectorStore


def build_rag_graph(llm: LLMClient, store: SimpleVectorStore, top_k: int = 4):
    def retrieve(state: RagState):
        return retrieve_node(state, store, top_k)

    def answer(state: RagState):
        return answer_node(state, llm)

    g = StateGraph(RagState)
    g.add_node("retrieve", retrieve)
    g.add_node("answer", answer)
    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "answer")
    g.add_edge("answer", END)
    return g.compile()

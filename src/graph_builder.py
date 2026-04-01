from langgraph.graph import END, START, StateGraph

from .agent_nodes import editor_node, research_node, writer_node
from .state import AgentState


def build_content_graph(llm):
    """
    Research -> Writer -> Editor 线性图。
    节点通过闭包捕获 llm；图内函数接收 AgentState，返回要合并进 state 的字段。
    """

    def research(state: AgentState):
        return {
            "research_summary": research_node(state["topic"], llm),
        }

    def writer(state: AgentState):
        return {
            "draft": writer_node(
                state["topic"],
                state["research_summary"],
                llm,
            ),
        }

    def editor(state: AgentState):
        return {
            "final_text": editor_node(state["topic"], state["draft"], llm),
        }

    g = StateGraph(AgentState)
    g.add_node("research", research)
    g.add_node("writer", writer)
    g.add_node("editor", editor)
    g.add_edge(START, "research")
    g.add_edge("research", "writer")
    g.add_edge("writer", "editor")
    g.add_edge("editor", END)
    return g.compile()

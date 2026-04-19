from langgraph.graph import END, START, StateGraph
from typing import Literal
from .agent_nodes import editor_node, research_node, writer_node, fact_checker_node, reviewer_node
from .state import AgentState

def after_fact_checker(state: AgentState) -> Literal["writer", "editor"]:
    status = state.get("fact_check_status", "需修改")
    if status == "严重错误":
        # 打回 writer 重写，并将 revised_draft 作为新的 draft 传入
        return "writer"
    else:
        # 通过或需修改（可自动修正） → 进入 editor 润色
        return "editor"
def after_reviewer(state: AgentState) -> Literal["editor","END"]:
    # 根据风格审查结果决定下一节点
    status = state.get("review_status", "通过")
    if status == "通过":
        return "END"
    else:
        # 有条件通过 或 不通过 → 回到 editor 再次润色（使用 revised_final 作为输入）
        return "editor"

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
            "final_text": editor_node(state["topic"], state["revised_draft"], llm),
        }

    def fact_checker(state: AgentState):
        result = fact_checker_node(state["topic"],state["research_summary"], state["draft"], llm)
        return {
            "fact_check_status": result.status,
            "fact_check_report": result.issues,
            "revised_draft": result.text
        }


    def reviewer(state: AgentState):
        result = reviewer_node(state["topic"], state["final_text"], llm)
        return {
            "review_status": result.status,
            "review_issues": result.issues,
            "revised_final": result.text
        }

    g = StateGraph(AgentState)
    g.add_node("research", research)
    g.add_node("writer", writer)
    g.add_node("editor", editor)
    g.add_node("fact_checker", fact_checker)
    g.add_node("reviewer", reviewer)
    g.add_edge(START, "research")
    g.add_edge("research", "writer")
    g.add_edge("writer", "fact_checker")
    g.add_conditional_edges("fact_checker", after_fact_checker,{
        "writer": "writer",
        "editor": "editor"
    })
    g.add_edge("editor", "reviewer")
    g.add_conditional_edges("reviewer", after_reviewer,{
        "editor": "editor",
        "END": END
    })
    return g.compile()

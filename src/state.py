from typing import TypedDict, List, Optional, Literal, Dict


class AgentState(TypedDict):
    """LangGraph 在节点间传递的共享状态。"""

    topic: str
    research_summary: str
    draft: str
    final_text: str

    fact_check_status: Optional[Literal["通过","需修改","严重错误"]]    
    fact_check_report: Optional[List[Dict[str, str]]]           # 事实核查的完整报告
    revised_draft: Optional[str]               # 事实核查后建议的修改稿
    review_status: Optional[Literal["通过", "有条件通过", "不通过"]]
    review_issues: Optional[List[Dict[str, str]]]        # 审查问题列表
    revised_final: Optional[str]               # reviewer 建议的修改版
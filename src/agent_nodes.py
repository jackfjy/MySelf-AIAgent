from .llm_client import LLMInput, LLMOutput
from .prompts import RESEARCH_PROMPT


def research_node(topic: str, llm) -> str:
    prompt = RESEARCH_PROMPT.format(topic=topic)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text


def writer_node(topic: str, research_summary: str, llm) -> str:
    """
    Step 3: Writer 节点（占位）。
    """
    raise NotImplementedError("writer_node not implemented yet")


def editor_node(topic: str, draft: str, llm) -> str:
    """
    Step 4: Editor 节点（占位）。
    """
    raise NotImplementedError("editor_node not implemented yet")


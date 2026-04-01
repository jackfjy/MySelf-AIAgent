from .llm_client import LLMInput, LLMOutput
from .prompts import EDITOR_PROMPT, RESEARCH_PROMPT, WRITER_PROMPT


def research_node(topic: str, llm) -> str:
    prompt = RESEARCH_PROMPT.format(topic=topic)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text


def writer_node(topic: str, research_summary: str, llm) -> str:
    prompt = WRITER_PROMPT.format(topic=topic, research_summary=research_summary)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text


def editor_node(topic: str, draft: str, llm) -> str:
    prompt = EDITOR_PROMPT.format(topic=topic, draft=draft)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text


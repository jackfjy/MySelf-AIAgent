from .llm_client import LLMInput, LLMOutput, LLMOutputJSON
from .prompts import EDITOR_PROMPT, FACT_CHECKER_PROMPT, RESEARCH_PROMPT, WRITER_PROMPT, REVIEWER_PROMPT
from .logger import log_node
import json

@log_node("research_node")
def research_node(topic: str, llm) -> str:
    prompt = RESEARCH_PROMPT.format(topic=topic)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text

@log_node("writer_node")
def writer_node(topic: str, research_summary: str, llm) -> str:
    prompt = WRITER_PROMPT.format(topic=topic, research_summary=research_summary)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text

@log_node("editor_node")
def editor_node(topic: str, draft: str, llm) -> str:
    prompt = EDITOR_PROMPT.format(topic=topic, draft=draft)
    out: LLMOutput = llm.invoke(LLMInput(prompt=prompt))
    return out.text

# @log_node("fact_checker_node")
def fact_checker_node(topic: str, research_summary: str, draft: str, llm) -> str:
    prompt =FACT_CHECKER_PROMPT.format(topic=topic, research_summary=research_summary, draft=draft)
    response =llm.invoke(LLMInput(prompt=prompt))
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    result = json.loads(text)
    return LLMOutputJSON(
        text=response.text,
        status=result["status"], 
        issues=result["issues"], 
        revised_text=result["revised_text"]
        ) 

# @log_node("reviewer_node")
def reviewer_node(topic: str, final_text: str, llm) -> str:
    prompt = REVIEWER_PROMPT.format(topic=topic, final_text=final_text)
    response = llm.invoke(LLMInput(prompt=prompt))
    text = response.text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    result = json.loads(text)
    return LLMOutputJSON(
        text=response.text,
        status=result["status"], 
        issues=result["issues"], 
        revised_text=result["revised_text"]
        ) 
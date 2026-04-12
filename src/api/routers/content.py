import asyncio

from fastapi import APIRouter, Request

from src.api.schemas import ContentGenerateRequest, ContentGenerateResponse
from src.services.content_service import run_content_generation

router = APIRouter()


@router.post("/generate", response_model=ContentGenerateResponse)
async def generate_content(body: ContentGenerateRequest, request: Request):
    def _run():
        return run_content_generation(
            request.app.state.llm,
            request.app.state.content_graph,
            body.topic,
        )

    state = await asyncio.to_thread(_run)
    return ContentGenerateResponse(
        topic=state["topic"],
        research_summary=state.get("research_summary", ""),
        draft=state.get("draft", ""),
        final_text=state.get("final_text", ""),
    )

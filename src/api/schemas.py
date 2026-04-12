from pydantic import BaseModel, Field, model_validator


class ContentGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=4000, description="文章主题")


class ContentGenerateResponse(BaseModel):
    topic: str
    research_summary: str
    draft: str
    final_text: str


class RagQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=8000)
    top_k: int = Field(4, ge=1, le=50)
    thread_id: str = Field("default", max_length=256)
    source_contains: str = Field("", max_length=512)
    rewrite: bool = False
    multi_query: bool = False
    multi_query_n: int = Field(3, ge=2, le=6)
    rerank: bool = False
    rerank_keep: int = Field(4, ge=1, le=20)

    @model_validator(mode="after")
    def rewrite_xor_multi(self):
        if self.rewrite and self.multi_query:
            raise ValueError("rewrite 与 multi_query 不能同时为 True")
        return self


class RagQueryResponse(BaseModel):
    retrieval_queries: list[str] = Field(default_factory=list)
    citations: str = ""
    answer: str


class RagReingestRequest(BaseModel):
    """从已保存的上传记录再次入库。"""

    ids: list[str] = Field(..., min_length=1, max_length=30)
    clear: bool = False
    max_chars: int = Field(800, ge=200, le=4000)

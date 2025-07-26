from typing import List, Optional
from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    document_ids: List[str] = Field(..., description="List of document IDs to index")


class IndexStatus(BaseModel):
    document_id: str
    status: str
    message: Optional[str] = None


class IndexResponse(BaseModel):
    results: List[IndexStatus]


class QueryRequest(BaseModel):
    document_ids: List[str] = Field(..., description="List of document IDs to query")
    question: str = Field(..., description="The question to answer")


class QueryResponse(BaseModel):
    run_id: str
    answer: str
    tokens_consumed: int
    tokens_generated: int
    response_time_ms: int
    confidence_score: float


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    chunk_index: int
    start_char: int
    end_char: int


class MetricsPayload(BaseModel):
    run_id: str
    agent_name: str = "rag-module"
    tokens_consumed: int
    tokens_generated: int
    response_time_ms: int
    confidence_score: float
    status: str
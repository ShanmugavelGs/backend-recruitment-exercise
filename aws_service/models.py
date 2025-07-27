from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class DocumentCreateRequest(BaseModel):
    doc_id: str
    filename: str
    tags: Optional[Dict[str, str]] = None
    s3_key: Optional[str] = None


class DocumentUpdateRequest(BaseModel):
    tags: Optional[Dict[str, str]] = None
    filename: Optional[str] = None


class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    upload_timestamp: datetime
    tags: Optional[Dict[str, str]] = None
    s3_key: Optional[str] = None


class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    upload_timestamp: datetime
    tags: Optional[Dict[str, str]] = None
    s3_key: Optional[str] = None


class IndexRequest(BaseModel):
    document_ids: List[str] = Field(..., description="List of document IDs to index")


class QueryRequest(BaseModel):
    document_ids: List[str] = Field(..., description="List of document IDs to query")
    question: str = Field(..., description="The question to answer")


class OperationResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
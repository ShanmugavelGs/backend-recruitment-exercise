from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    doc_id: str
    filename: str
    upload_timestamp: datetime
    file_size: int
    page_count: Optional[int] = None
    text_length: Optional[int] = None


class DocumentResponse(BaseModel):
    doc_id: str
    filename: str
    upload_timestamp: datetime
    file_size: int
    page_count: Optional[int] = None
    text_length: Optional[int] = None
    extracted_text: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]
    total: int
    page: int
    limit: int
    total_pages: int


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    upload_timestamp: datetime
    file_size: int
    page_count: Optional[int] = None
    status: str = "success"
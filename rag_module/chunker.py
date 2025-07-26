import os
import uuid
from typing import List
from .models import DocumentChunk


class TextChunker:
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or int(os.getenv("CHUNK_SIZE", "1000"))
        self.overlap = overlap or int(os.getenv("CHUNK_OVERLAP", "200"))

    def chunk_text(self, document_id: str, text: str) -> List[DocumentChunk]:
        if not text.strip():
            return []

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            if start == 0:
                end = min(start + self.chunk_size, len(text))
            else:
                end = min(start + self.chunk_size - self.overlap, len(text))

            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunk = DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end
                )
                chunks.append(chunk)
                chunk_index += 1

            if end >= len(text):
                break
            
            start = end - self.overlap if chunk_index > 0 else end

        return chunks

    def chunk_documents(self, documents: dict) -> List[DocumentChunk]:
        all_chunks = []
        for doc_id, text in documents.items():
            chunks = self.chunk_text(doc_id, text)
            all_chunks.extend(chunks)
        return all_chunks
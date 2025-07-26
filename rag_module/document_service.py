import os
import httpx
from typing import Dict, Optional


class DocumentService:
    def __init__(self):
        self.pdf_service_url = os.getenv("PDF_SERVICE_URL", "http://pdf_service:8000")
        self.timeout = float(os.getenv("PDF_SERVICE_TIMEOUT", "30.0"))

    async def get_document_text(self, document_id: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.pdf_service_url}/pdf/documents/{document_id}"
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return data.get("extracted_text")
        except Exception as e:
            print(f"Failed to fetch document {document_id}: {str(e)}")
            return None

    async def get_documents_text(self, document_ids: list[str]) -> Dict[str, str]:
        documents = {}
        for doc_id in document_ids:
            text = await self.get_document_text(doc_id)
            if text:
                documents[doc_id] = text
        return documents
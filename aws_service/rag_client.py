import os
import httpx
from typing import Dict, Any


class RAGClient:
    def __init__(self):
        self.rag_service_url = os.getenv("RAG_SERVICE_URL", "http://rag_module:8001")
        self.timeout = float(os.getenv("RAG_SERVICE_TIMEOUT", "60.0"))

    async def index_documents(self, document_ids: list[str]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.rag_service_url}/rag/index",
                    json={"document_ids": document_ids}
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise ValueError("RAG service timeout during indexing")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"RAG service indexing failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"Failed to communicate with RAG service: {str(e)}")

    async def query_documents(self, document_ids: list[str], question: str) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.rag_service_url}/rag/query",
                    json={
                        "document_ids": document_ids,
                        "question": question
                    }
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            raise ValueError("RAG service timeout during query")
        except httpx.HTTPStatusError as e:
            raise ValueError(f"RAG service query failed: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise ValueError(f"Failed to communicate with RAG service: {str(e)}")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.rag_service_url}/health")
                return response.status_code == 200
        except:
            return False
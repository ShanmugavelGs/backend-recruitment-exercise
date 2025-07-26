import os
from typing import List
from openai import OpenAI

class EmbeddingService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise ValueError(f"Failed to create embeddings: {str(e)}")

    async def create_embedding(self, text: str) -> List[float]:
        embeddings = await self.create_embeddings([text])
        return embeddings[0]
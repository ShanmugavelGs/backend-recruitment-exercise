import os
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from .models import DocumentChunk


class VectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = os.getenv("PINECONE_INDEX", "vector")
        self.dimension = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
        self.metric = os.getenv("PINECONE_METRIC", "cosine")
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")
        
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index_exists(self):
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                    cloud=self.cloud,
                    region=self.region
                )
            )

    async def upsert_chunks(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vector = {
                'id': chunk.chunk_id,
                'values': embedding,
                'metadata': {
                    'document_id': chunk.document_id,
                    'text': chunk.text,
                    'chunk_index': chunk.chunk_index,
                    'start_char': chunk.start_char,
                    'end_char': chunk.end_char
                }
            }
            vectors.append(vector)

        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)

    async def query_similar_chunks(
        self, 
        query_embedding: List[float], 
        document_ids: List[str], 
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        top_k = top_k or int(os.getenv("TOP_K", "5"))
        
        filter_dict = {"document_id": {"$in": document_ids}} if document_ids else None
        
        response = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
            filter=filter_dict
        )
        
        return [
            {
                'id': match.id,
                'score': match.score,
                'text': match.metadata.get('text', ''),
                'document_id': match.metadata.get('document_id', ''),
                'chunk_index': match.metadata.get('chunk_index', 0)
            }
            for match in response.matches
        ]

    async def delete_document_chunks(self, document_id: str):
        self.index.delete(filter={"document_id": document_id})
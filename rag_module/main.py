import os
import time
import uuid
from typing import List
from fastapi import FastAPI, HTTPException

from .models import (
    IndexRequest, IndexResponse, IndexStatus,
    QueryRequest, QueryResponse, MetricsPayload
)
from .chunker import TextChunker
from .embeddings import EmbeddingService
from .vector_store import VectorStore
from .llm_service import LLMService
from .metrics_client import MetricsClient
from .document_service import DocumentService

app = FastAPI(title="RAG Module", version="1.0.0")

chunker = TextChunker()
embedding_service = EmbeddingService()
vector_store = VectorStore()
llm_service = LLMService()
metrics_client = MetricsClient()
document_service = DocumentService()


@app.post("/rag/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest):
    results = []
    
    for doc_id in request.document_ids:
        try:
            text = await document_service.get_document_text(doc_id)
            if not text:
                results.append(IndexStatus(
                    document_id=doc_id,
                    status="failed",
                    message="Document not found or empty"
                ))
                continue

            chunks = chunker.chunk_text(doc_id, text)
            if not chunks:
                results.append(IndexStatus(
                    document_id=doc_id,
                    status="failed",
                    message="No chunks generated from document"
                ))
                continue

            chunk_texts = [chunk.text for chunk in chunks]
            embeddings = await embedding_service.create_embeddings(chunk_texts)
            
            await vector_store.upsert_chunks(chunks, embeddings)
            
            results.append(IndexStatus(
                document_id=doc_id,
                status="success",
                message=f"Indexed {len(chunks)} chunks"
            ))

        except Exception as e:
            results.append(IndexStatus(
                document_id=doc_id,
                status="failed",
                message=str(e)
            ))

    return IndexResponse(results=results)


@app.post("/rag/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    start_time = time.time()
    run_id = str(uuid.uuid4())

    try:
        query_embedding = await embedding_service.create_embedding(request.question)
        
        similar_chunks = await vector_store.query_similar_chunks(
            query_embedding=query_embedding,
            document_ids=request.document_ids
        )

        if not similar_chunks:
            raise HTTPException(
                status_code=404,
                detail="No relevant content found for the given question and documents"
            )

        answer, tokens_consumed, tokens_generated, confidence_score = await llm_service.generate_answer(
            question=request.question,
            context_chunks=similar_chunks
        )

        response_time_ms = int((time.time() - start_time) * 1000)

        metrics = MetricsPayload(
            run_id=run_id,
            tokens_consumed=tokens_consumed,
            tokens_generated=tokens_generated,
            response_time_ms=response_time_ms,
            confidence_score=confidence_score,
            status="success"
        )

        await metrics_client.send_metrics(metrics)

        return QueryResponse(
            run_id=run_id,
            answer=answer,
            tokens_consumed=tokens_consumed,
            tokens_generated=tokens_generated,
            response_time_ms=response_time_ms,
            confidence_score=confidence_score
        )

    except HTTPException:
        raise
    except Exception as e:
        response_time_ms = int((time.time() - start_time) * 1000)
        
        metrics = MetricsPayload(
            run_id=run_id,
            tokens_consumed=0,
            tokens_generated=0,
            response_time_ms=response_time_ms,
            confidence_score=0.0,
            status="failed"
        )

        await metrics_client.send_metrics(metrics)
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rag_module"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
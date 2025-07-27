import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException

from .models import (
    DocumentCreateRequest, DocumentUpdateRequest, DocumentResponse,
    IndexRequest, QueryRequest, OperationResponse
)
from .dynamodb_service import DynamoDBService
from .s3_service import S3Service
from .rag_client import RAGClient

app = FastAPI(title="AWS Service", version="1.0.0")

dynamodb_service = DynamoDBService()
s3_service = S3Service()
rag_client = RAGClient()


@app.post("/aws/documents", response_model=DocumentResponse)
async def create_document(request: DocumentCreateRequest):
    try:
        document = await dynamodb_service.create_document(
            doc_id=request.doc_id,
            filename=request.filename,
            tags=request.tags,
            s3_key=request.s3_key
        )
        
        return DocumentResponse(
            doc_id=document.doc_id,
            filename=document.filename,
            upload_timestamp=document.upload_timestamp,
            tags=document.tags,
            s3_key=document.s3_key
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/aws/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    document = await dynamodb_service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        doc_id=document.doc_id,
        filename=document.filename,
        upload_timestamp=document.upload_timestamp,
        tags=document.tags,
        s3_key=document.s3_key
    )


@app.put("/aws/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(doc_id: str, request: DocumentUpdateRequest):
    document = await dynamodb_service.update_document(
        doc_id=doc_id,
        tags=request.tags,
        filename=request.filename
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        doc_id=document.doc_id,
        filename=document.filename,
        upload_timestamp=document.upload_timestamp,
        tags=document.tags,
        s3_key=document.s3_key
    )


@app.delete("/aws/documents/{doc_id}", response_model=OperationResponse)
async def delete_document(doc_id: str):
    document = await dynamodb_service.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        if document.s3_key:
            await s3_service.delete_file(document.s3_key)
        
        success = await dynamodb_service.delete_document(doc_id)
        
        if success:
            return OperationResponse(
                success=True,
                message="Document deleted successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document from DynamoDB")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")


@app.post("/aws/documents/{doc_id}/index", response_model=OperationResponse)
async def index_document(doc_id: str):
    if not await dynamodb_service.document_exists(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        result = await rag_client.index_documents([doc_id])
        
        # Check if indexing was successful
        if result.get("results") and len(result["results"]) > 0:
            doc_result = result["results"][0]
            if doc_result.get("status") == "success":
                return OperationResponse(
                    success=True,
                    message="Document indexed successfully",
                    data=result
                )
            else:
                return OperationResponse(
                    success=False,
                    message=doc_result.get("message", "Indexing failed"),
                    data=result
                )
        else:
            return OperationResponse(
                success=False,
                message="No indexing results returned"
            )
            
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing error: {str(e)}")


@app.post("/aws/query", response_model=Dict[str, Any])
async def query_documents(request: QueryRequest):
    for doc_id in request.document_ids:
        if not await dynamodb_service.document_exists(doc_id):
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    
    try:
        result = await rag_client.query_documents(
            document_ids=request.document_ids,
            question=request.question
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "aws_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
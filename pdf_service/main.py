import os
import uuid
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException, Query

from .models import DocumentResponse, DocumentListResponse, UploadResponse
from .storage import DocumentStorage
from .pdf_processor import PDFProcessor

app = FastAPI(title="PDF Service", version="1.0.0")

storage = DocumentStorage(storage_dir=os.getenv("STORAGE_DIR", "uploads"))
pdf_processor = PDFProcessor()


@app.post("/pdf/upload", response_model=List[UploadResponse])
async def upload_pdfs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    results = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} is not a PDF"
            )
        
        content = await file.read()
        
        if not pdf_processor.is_valid_pdf(content):
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} is not a valid PDF"
            )
        
        try:
            extracted_text, page_count = pdf_processor.extract_text_and_metadata(content)
            doc_id = str(uuid.uuid4())
            
            metadata = storage.save_document(
                doc_id=doc_id,
                filename=file.filename,
                content=content,
                extracted_text=extracted_text,
                page_count=page_count
            )
            
            results.append(UploadResponse(
                doc_id=metadata.doc_id,
                filename=metadata.filename,
                upload_timestamp=metadata.upload_timestamp,
                file_size=metadata.file_size,
                page_count=metadata.page_count
            ))
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    return results


@app.get("/pdf/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    metadata = storage.get_document_metadata(doc_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Document not found")
    
    extracted_text = storage.get_document_text(doc_id)
    if extracted_text is None:
        raise HTTPException(status_code=500, detail="Document text not found")
    
    return DocumentResponse(
        doc_id=metadata.doc_id,
        filename=metadata.filename,
        upload_timestamp=metadata.upload_timestamp,
        file_size=metadata.file_size,
        page_count=metadata.page_count,
        text_length=metadata.text_length,
        extracted_text=extracted_text
    )


@app.get("/pdf/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    documents, total = storage.get_all_documents(page=page, limit=limit)
    total_pages = (total + limit - 1) // limit
    
    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "pdf_service"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
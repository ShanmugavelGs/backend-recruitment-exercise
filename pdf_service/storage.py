import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import DocumentMetadata

class DocumentStorage:
    def __init__(self, storage_dir: str = "uploads"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.metadata_file = self.storage_dir / "metadata.json"
        self._load_metadata()

    def _load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                self.metadata = {
                    doc_id: DocumentMetadata(**meta) 
                    for doc_id, meta in data.items()
                }
        else:
            self.metadata = {}

    def _save_metadata(self):
        data = {
            doc_id: meta.model_dump(mode='json')
            for doc_id, meta in self.metadata.items()
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def save_document(self, doc_id: str, filename: str, content: bytes, 
                     extracted_text: str, page_count: Optional[int] = None) -> DocumentMetadata:   
        pdf_path = self.storage_dir / f"{doc_id}.pdf"
        text_path = self.storage_dir / f"{doc_id}.txt"
        
        with open(pdf_path, 'wb') as f:
            f.write(content)
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        metadata = DocumentMetadata(
            doc_id=doc_id,
            filename=filename,
            upload_timestamp=datetime.utcnow(),
            file_size=len(content),
            page_count=page_count,
            text_length=len(extracted_text)
        )
        
        self.metadata[doc_id] = metadata
        self._save_metadata()
        return metadata

    def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        return self.metadata.get(doc_id)

    def get_document_text(self, doc_id: str) -> Optional[str]:
        text_path = self.storage_dir / f"{doc_id}.txt"
        if text_path.exists():
            with open(text_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def get_all_documents(self, page: int = 1, limit: int = 10) -> tuple[List[DocumentMetadata], int]:
        all_docs = list(self.metadata.values())
        all_docs.sort(key=lambda x: x.upload_timestamp, reverse=True)
        
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        return all_docs[start_idx:end_idx], len(all_docs)

    def document_exists(self, doc_id: str) -> bool:
        return doc_id in self.metadata


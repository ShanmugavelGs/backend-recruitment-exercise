import io
from typing import Tuple, Optional
import pymupdf


class PDFProcessor:
    @staticmethod
    def extract_text_and_metadata(pdf_content: bytes) -> Tuple[str, Optional[int]]:
        try:
            # Load PDF from in-memory bytes
            pdf_stream = io.BytesIO(pdf_content)
            doc = pymupdf.open(stream=pdf_stream, filetype="pdf")
            
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            
            extracted_text = "\n".join(text_parts)
            page_count = len(doc)
            return extracted_text, page_count

        except Exception as e:
            raise ValueError(f"Failed to process PDF: {str(e)}")

    @staticmethod
    def is_valid_pdf(content: bytes) -> bool:
        try:
            doc = pymupdf.open(stream=content, filetype="pdf")
            return len(doc) > 0
        except:
            return False

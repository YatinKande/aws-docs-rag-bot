import os
from typing import List, Dict, Any
from pypdf import PdfReader
from backend.utils.chunking import Chunker

class DocumentProcessor:
    def __init__(self):
        self.chunker = Chunker()

    async def process_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Extracts text and splits into chunks with metadata."""
        ext = filename.split(".")[-1].lower()
        text = ""
        
        if ext == "pdf":
            text = self._extract_pdf(file_path)
        elif ext in ["txt", "md"]:
            text = self._extract_text(file_path)
        # Add more logic for DOCX, CSV etc later
        
        if not text:
            return []

        chunks = self.chunker.split_text(text)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                "content": chunk,
                "metadata": {
                    "source": filename,
                    "chunk_index": i,
                    "file_type": ext
                }
            })
        return processed_chunks

    def _extract_pdf(self, path: str) -> str:
        text = ""
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text

    def _extract_text(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""

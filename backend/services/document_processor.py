import os
import json
import csv
import io
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# New libraries
from unstructured.partition.auto import partition
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import asyncio
import time
import pypdf

from backend.utils.chunking import Chunker
from backend.core.config import settings
from backend.utils.service_detection import get_service_from_filename

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.chunker = Chunker()
        self._llm_service = None # Lazy load to avoid circular imports

    @property
    def llm_service(self):
        if self._llm_service is None:
            from backend.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    async def process_file(self, file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Processes any file type using unstructured or custom OCR/Vision logic."""
        ext = filename.split(".")[-1].lower()
        text = ""
        
        logger.info(f"Processing {filename} (extension: {ext})")

        try:
            # 1. Handle Images (Direct to Ollama Vision)
            if ext in ["jpg", "jpeg", "png", "bmp", "gif"]:
                text = await self._process_image_with_vision(file_path)
            
            # 2. Handle PDFs with OCR Check
            elif ext == "pdf":
                text = await asyncio.get_event_loop().run_in_executor(None, self._process_pdf_smart, file_path)
            
            # 3. Universal Parsing for everything else
            else:
                text = await asyncio.get_event_loop().run_in_executor(None, self._process_universal, file_path)

        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            # Fallback to simple extractors if unstructured fails
            text = self._fallback_extraction(file_path, ext)

        if not text:
            return []

        # Chunking
        chunks = self.chunker.split_text(text)
        
        # Metadata construction
        service = get_service_from_filename(filename)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                "content": chunk,
                "metadata": {
                    "source": filename,
                    "file_type": ext,
                    "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "chunk_index": i,
                    "source_topic": service, # Using service as a proxy for topic
                    "doc_category": "knowledge_base"
                }
            })
        
        logger.info(f"Successfully processed {filename} into {len(processed_chunks)} chunks.")
        return processed_chunks

    async def _process_image_with_vision(self, file_path: str) -> str:
        """Uses Ollama Vision (LLaVA) + OCR for high-fidelity image understanding."""
        # OCR
        ocr_text = ""
        try:
            img = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception as e:
            logger.warning(f"OCR failed for {file_path}: {e}")

        # LLM Vision Description
        description = await self.llm_service.describe_image(file_path)
        
        combined = []
        if ocr_text:
            combined.append(f"EXTRACTED TEXT:\n{ocr_text}")
        if description:
            combined.append(f"VISUAL DESCRIPTION:\n{description}")
            
        return "\n\n".join(combined)

    def _process_pdf_smart(self, file_path: str) -> str:
        """Optimized PDF processing with fast path (pypdf) and fallback to unstructured/OCR."""
        start_time = time.time()
        text = ""

        # Phase 1: FAST PATH with pypdf
        try:
            logger.info(f"Attempting Fast Path extraction (pypdf) for {file_path}")
            reader = pypdf.PdfReader(file_path)
            extracted_text = []
            for page in reader.pages:
                extracted_text.append(page.extract_text() or "")
            text = "\n\n".join(extracted_text)
            
            if len(text.strip()) > 200:
                logger.info(f"Fast Path (pypdf) successful. Extracted {len(text)} chars in {time.time() - start_time:.2f}s")
                return text
        except Exception as e:
            logger.warning(f"Fast Path (pypdf) failed: {e}")

        # Phase 2: STRUCTURAL PATH with unstructured (using 'fast' strategy)
        try:
            logger.info(f"Attempting Structural Path (unstructured fast) for {file_path}")
            elements = partition(filename=file_path, strategy="fast")
            text = "\n\n".join([str(el) for el in elements])
        except Exception as e:
            logger.error(f"Structural Path (unstructured) failed: {e}")

        # Phase 3: VISION PATH (OCR) if text is empty/insufficient
        if len(text.strip()) < 100:
            logger.info("Insufficient text in PDF. Attempting OCR Vision Path...")
            try:
                images = convert_from_path(file_path)
                ocr_parts = []
                for i, image in enumerate(images):
                    page_text = pytesseract.image_to_string(image)
                    ocr_parts.append(page_text)
                text = "\n\n".join(ocr_parts)
            except Exception as e:
                logger.error(f"Vision Path (OCR) failed: {e}")
        
        logger.info(f"PDF processing (hybrid) completed in {time.time() - start_time:.2f}s")
        return text

    def _process_universal(self, file_path: str) -> str:
        """Uses 'unstructured' to partition various document formats."""
        elements = partition(filename=file_path)
        return "\n\n".join([str(el) for el in elements])

    def _fallback_extraction(self, path: str, ext: str) -> str:
        """Simple fallback if unstructured/smart processing fails."""
        try:
            if ext in ["txt", "md"]:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            elif ext == "json":
                with open(path, "r", encoding="utf-8") as f:
                    return json.dumps(json.load(f), indent=2)
            # Add more fallbacks if needed
        except:
            pass
        return ""

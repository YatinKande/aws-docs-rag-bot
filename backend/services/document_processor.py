import os
import json
import csv
import io
import logging
import zipfile
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# New libraries
import aiofiles
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
        self.concurrency_limit = 10
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)
        from backend.services.s3_sync import s3_sync_manager
        self.s3_manager = s3_sync_manager

    @property
    def llm_service(self):
        if self._llm_service is None:
            from backend.services.llm_service import LLMService
            self._llm_service = LLMService()
        return self._llm_service

    async def process_file(self, file_path: str, filename: str, skip_val_check: bool = False) -> List[Dict[str, Any]]:
        """Processes any file type using unstructured or custom OCR/Vision logic."""
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        
        # Guard: Skip obvious low-value files (icons, small images) to prevent hanging on massive ZIPs
        if not skip_val_check and ext in ["png", "jpg", "jpeg", "svg", "ico"]:
            try:
                if os.path.getsize(file_path) < 50000: # < 50KB is likely an icon
                    logger.info(f"Skipping potential icon/low-value asset: {filename}")
                    return []
            except:
                pass

        logger.info(f"Processing {filename} (extension: {ext})")
        text = ""

        try:
            # 1. Handle Images (OCR + Vision)
            if ext in ["jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp"]:
                text = await self._process_image_with_vision(file_path)
            
            # 2. Handle PDFs (Smart Hybrid)
            elif ext == "pdf":
                text = await asyncio.get_event_loop().run_in_executor(None, self._process_pdf_smart, file_path)
            
            # 3. Handle Office Docs (Recursive/Subfolders supported)
            elif ext in ["docx", "pptx", "xlsx", "xls", "csv"]:
                text = await asyncio.get_event_loop().run_in_executor(None, self._process_universal, file_path)
            
            # 4. Handle Zip Files (Deep Recursion)
            elif ext == "zip":
                return await self._process_zip_recursive(file_path)
            
            # 5. Handle Text/Code Files
            elif ext in ["txt", "md", "json", "yaml", "py", "js", "sql", "sh", "html"]:
                try:
                    async with aiofiles.open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
                        text = await f.read()
                except:
                    text = self._fallback_extraction(file_path, ext)
            
            # 6. Fallback
            else:
                text = await asyncio.get_event_loop().run_in_executor(None, self._process_universal, file_path)

        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")
            text = self._fallback_extraction(file_path, ext)

        if not text:
            return []

        return self._create_chunks(text, filename, ext)

    def _create_chunks(self, text: str, filename: str, ext: str) -> List[Dict[str, Any]]:
        """Handles chunking and metadata standardizing with Semantic chunking."""
        from semantic_text_splitter import TextSplitter
        
        service = get_service_from_filename(filename)
        
        from tokenizers import Tokenizer
        
        tokenizer = Tokenizer.from_pretrained("BAAI/bge-m3")
        splitter = TextSplitter.from_huggingface_tokenizer(
            tokenizer,
            capacity=(256, 512),  # min/max tokens
            overlap=50
        )
        
        chunks = splitter.chunks(text)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) <= 50:
                continue
                
            processed_chunks.append({
                "content": chunk,
                "metadata": {
                    "source": filename,
                    "file_type": ext,
                    "upload_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "chunk_index": i,
                    "source_topic": service,
                    "doc_category": "knowledge_base",
                    "chunk_size": len(chunk),
                    "chunking": "semantic"
                }
            })
        return processed_chunks

    async def _process_image_with_vision(self, file_path: str) -> str:
        """Uses Ollama Vision (LLaVA) + OCR for high-fidelity image understanding."""
        ocr_text = ""
        try:
            img = Image.open(file_path)
            ocr_text = pytesseract.image_to_string(img).strip()
        except Exception as e:
            logger.warning(f"OCR failed for {file_path}: {e}")

        description = await self.llm_service.describe_image(file_path)
        
        combined = []
        if ocr_text:
            combined.append(f"EXTRACTED TEXT:\n{ocr_text}")
        if description and not description.startswith("Error"):
            combined.append(f"VISUAL DESCRIPTION:\n{description}")
            
        return "\n\n".join(combined)

    def _process_pdf_smart(self, file_path: str) -> str:
        """Optimized PDF processing (Hybrid Path)."""
        text = ""
        try:
            reader = pypdf.PdfReader(file_path)
            text = "\n\n".join([p.extract_text() or "" for p in reader.pages])
            if len(text.strip()) > 300:
                return text
        except:
            pass

        try:
            elements = partition(filename=file_path)
            text = "\n\n".join([str(el) for el in elements])
        except:
            pass

        if len(text.strip()) < 100:
            try:
                images = convert_from_path(file_path)
                text = "\n\n".join([pytesseract.image_to_string(img) for img in images])
            except:
                pass
        return text

    async def _process_zip_recursive(self, zip_path: str) -> List[Dict[str, Any]]:
        """Deep recursive extraction with S3-native focus."""
        all_chunks = []
        report = {"processed": 0, "skipped": 0, "failed": 0, "files": []}
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(tmp_dir)
                
                tasks = []
                for root, _, files in os.walk(tmp_dir):
                    for fname in files:
                        if fname.startswith('.') or "__MACOSX" in root:
                            continue
                        fpath = os.path.join(root, fname)
                        tasks.append(self._sem_process(fpath, fname))
                
                results = await asyncio.gather(*tasks)
                for res in results:
                    if res:
                        all_chunks.extend(res)
                        report["processed"] += 1
                    else:
                        report["skipped"] += 1
                
                logger.info(f"ZIP Recursive Processed: {report['processed']} files, {len(all_chunks)} chunks.")
            except Exception as e:
                logger.error(f"ZIP Processing error: {e}")
        
        return all_chunks

    async def _sem_process(self, fpath: str, fname: str):
        """Semaphore-guarded parallel process."""
        async with self.semaphore:
            return await self.process_file(fpath, fname)

    def _process_universal(self, file_path: str) -> str:
        """Uses 'unstructured' for DOCX, PPTX, XLSX."""
        try:
            elements = partition(filename=file_path)
            return "\n\n".join([str(el) for el in elements])
        except Exception as e:
            logger.warning(f"Universal partition failed: {e}")
            return ""

    def _fallback_extraction(self, path: str, ext: str) -> str:
        """Safe fallback to plain text."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(50000)
        except:
            return ""

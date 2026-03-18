"""
Retrieval Service
- Orchestrates document ingestion and semantic search
- Implements robust error handling with loguru
- Fixes UTC deprecation and improves logging
"""
from loguru import logger
import asyncio
import time
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.services.retrieval.advanced_retrieval import AdvancedRetrieval
from backend.services.document_processor import DocumentProcessor
from backend.models.models import Document
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.config import settings
from backend.utils.service_detection import (
    get_service_from_filename, 
    get_display_name, 
    get_service_filter
)
from backend.services.s3_sync import s3_sync_manager
from backend.utils.source_validator import register_document, remove_document

class RetrievalService:
    # A simple in-memory cache for processed document chunks to prevent re-running 
    # expensive Vision/OCR when switching databases for the same file.
    _ingestion_cache = {} 

    def __init__(self):
        self.engine = AdvancedRetrieval()
        self.doc_processor = DocumentProcessor()
        from backend.services.llm_service import LLMService
        self.llm_service = LLMService()

    async def _update_status(self, db: AsyncSession, document_id: str, status: str):
        """Helper to update document status in the DB."""
        try:
            if db and document_id:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.status = status
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to update status for {document_id}: {e}")

    async def add_to_all_stores(self, documents: List[Dict[str, Any]]):
        """Proxies batch ingestion to all stores."""
        try:
            await self.engine.add_to_all_stores(documents)
        except Exception as e:
            logger.error(f"RetrievalService add_to_all_stores failed: {e}")

    async def ingest_document(
        self, 
        file_path: str, 
        filename: str, 
        database: str = "faiss", 
        document_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Processes a file and adds it to the advanced retrieval engine."""
        chunks = []
        try:
            if document_id and db:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.status = "processing"
                    await db.commit()

            # Check if we've already processed this file in this session
            cache_key = file_path
            if cache_key in self._ingestion_cache:
                await self._update_status(db, document_id, "ingesting (cached)")
                logger.info(f"Using cached chunks for {filename} (skipping Vision/OCR)")
                chunks = self._ingestion_cache[cache_key]
            else:
                await self._update_status(db, document_id, "analyzing content...")
                
                # Check if file exists locally, otherwise pull from S3
                if not os.path.exists(file_path):
                    logger.info(f"File {filename} missing locally. Attempting to pull from S3...")
                    logger.info(f"File {filename} missing locally. Attempting to pull from S3...")
                    service = get_service_from_filename(filename)
                    try:
                        await s3_sync_manager.download_document(filename, service, file_path)
                    except Exception as s3e:
                        logger.error(f"Failed to restore {filename} from S3: {s3e}")
                        # If S3 fails, we can't process
                        await self._update_status(db, document_id, "failed (file missing)")
                        return 0, []

                start_proc = time.time()
                logger.info(f"RetrievalService: Calling DocumentProcessor for {filename}...")
                chunks = await self.doc_processor.process_file(file_path, filename)
                logger.info(f"RetrievalService: {len(chunks)} chunks returned for {filename} in {time.time() - start_proc:.2f}s")
                # Cache results for other databases
                if chunks:
                    self._ingestion_cache[cache_key] = chunks
            
            if chunks:
                service = get_service_from_filename(filename)
                display_name = get_display_name(service)
                
                # Standardize metadata BEFORE vectorization
                for i, chunk in enumerate(chunks):
                    # Ensure it is a dict for consistency
                    if hasattr(chunk, 'metadata'):
                        chunk.metadata.update({
                            "source":       filename,
                            "service":      service,
                            "source_topic": service, # Standard key used for filtering
                            "doc_type":     "official_aws_doc",
                            "chunk_index":  i,
                            "display_name": display_name
                        })
                    elif isinstance(chunk, dict):
                        meta = chunk.get("metadata", {})
                        meta.update({
                            "source":       filename,
                            "service":      service,
                            "source_topic": service,
                            "doc_type":     "official_aws_doc",
                            "chunk_index":  i,
                            "display_name": display_name
                        })
                        chunk["metadata"] = meta
                
                logger.info(f"RetrievalService: Starting vectorization of {len(chunks)} chunks into {database}...")
                await self._update_status(db, document_id, f"vectorizing into {database}...")
                
                # Set a critical timeout of 1800 seconds for vectorization (increased for large docs)
                try:
                    start_vec = time.time()
                    await asyncio.wait_for(self.engine.add_documents(chunks, database=database), timeout=1800.0)
                    logger.info(f"Vectorization for {filename} into {database} took {time.time() - start_vec:.2f}s")

                    # Register doc in the master registry
                    register_document(filename, service)
                    
                    if document_id and db:
                        doc = await db.get(Document, document_id)
                        if doc:
                            doc.status = "completed"
                            doc.processed = True
                            meta = dict(doc.metadata_info or {})
                            meta["chunks"] = len(chunks)
                            meta["processed_at"] = datetime.now(timezone.utc).isoformat()
                            doc.metadata_info = meta
                            from sqlalchemy.orm.attributes import flag_modified
                            flag_modified(doc, "metadata_info")
                            await db.commit()
                            logger.info(f"Successfully processed {filename}: {len(chunks)} chunks")
                            
                            # Sync updated index to S3 (non-blocking)
                            await s3_sync_manager.sync_index_to_s3()
                except asyncio.TimeoutError:
                    logger.error(f"TIMEOUT: Vectorization for {filename} took too long (>1800s)")
                    await self._update_status(db, document_id, "failed (timeout)")
                    return 0, []
            else:
                if document_id and db:
                    doc = await db.get(Document, document_id)
                    if doc:
                        doc.status = "failed"
                        await db.commit()
                        
        except Exception as e:
            logger.critical(f"CRITICAL ERROR in RetrievalService: {str(e)}")
            await self._update_status(db, document_id, f"failed: {str(e)[:50]}")
            if db:
                await db.rollback()
            return 0, []
                
        return len(chunks) if chunks else 0, chunks

    def is_document_in_index(self, filename: str) -> bool:
        """Checks if a document is already indexed in FAISS."""
        return self.engine.is_document_in_index(filename)

    async def semantic_search(self, query: str, top_k: int = 5, database: str = "faiss") -> List[Dict[str, Any]]:
        """Performs advanced retrieval with intent classification and metadata filtering."""
        try:
            # 1. Classify Intent & Extract Topic
            intent_info = await self.llm_service.classify_intent(query)
            topic = intent_info.get("topic")
            
            # 2. Build Metadata Filter
            filter_dict = {}
            if topic:
                topic = topic.lower() # Case-insensitive normalization
                filter_dict["source_topic"] = topic
                logger.debug(f"Applying Intent Topic Filter: {topic}")
            
            # Fallback to keyword-based filtering if no topic from LLM
            if not filter_dict:
                filter_dict = get_service_filter(query)
                if filter_dict:
                    logger.debug(f"Applying Keyword Service Filter: {filter_dict}")
                
            # 3. Search & Rerank
            results = await self.engine.search(query, top_k=top_k, database=database, filter=filter_dict)
            
            # 4. Apply Confidence Threshold
            threshold = settings.RETRIEVAL_CONFIDENCE_THRESHOLD
            
            filtered_results = []
            for res in results:
                score = res.get("rerank_score", 0.5) 
                if score >= threshold:
                    filtered_results.append(res)
                    
            if not filtered_results and results:
                logger.warning(f"Best result score {results[0].get('rerank_score')} below threshold {threshold}.")
                
            return filtered_results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    async def delete_document(self, filename: str, database: str = "faiss"):
        """Removes a document's chunks from the vector store and registry."""
        try:
            await self.engine.delete_documents({"source": filename}, database=database)
            
            remove_document(filename)
            logger.info(f"Cleaned up indices for {filename}")

            # Sync updated index to S3 (non-blocking)
            await s3_sync_manager.sync_index_to_s3()
        except Exception as e:
            logger.error(f"Failed to delete document {filename}: {e}")

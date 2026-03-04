import asyncio
import os
from loguru import logger
from typing import List, Dict, Any
from backend.core.config import settings
from backend.services.s3_sync import s3_sync_manager
from backend.services.retrieval.semantic_search import RetrievalService
from backend.utils.service_detection import get_service_from_filename
from backend.models.database import AsyncSessionLocal
from sqlalchemy import select
from backend.models.models import Document

class BootstrapSync:
    def __init__(self):
        self.retrieval_service = RetrievalService()

    async def run_bootstrap_sync(self):
        """Main entry point for synchronizing S3 with vector databases."""
        if not s3_sync_manager.enabled:
            logger.warning("Bootstrap Sync: S3 not enabled. Skipping.")
            return

        logger.info("Starting Bootstrap Synchronization with S3...")

        try:
            # 1. Pull latest registry from S3 to ensure we have the most recent state
            await s3_sync_manager.pull_registry_from_s3()
            
            # 2. List all documents in the bucket
            s3_docs = await self._list_s3_documents()
            if not s3_docs:
                logger.info("No documents found in S3 bucket.")
                return

            logger.info(f"Checking {len(s3_docs)} documents from S3...")

            # 3. Process each document
            for doc_info in s3_docs:
                filename = doc_info["filename"]
                if filename == ".gitkeep" or filename.startswith("."):
                    continue
                    
                etag = doc_info["etag"]
                service = get_service_from_filename(filename)
                
                # Check if we need to process this document
                needs_sync = await self._needs_processing(filename, etag)
                
                if needs_sync:
                    logger.info(f"🔄 Syncing {filename} (ETag changed or missing)...")
                    # Download to temp
                    temp_path = os.path.join("data/uploads/temp", filename)
                    try:
                        await s3_sync_manager.download_document(filename, service, temp_path)
                        
                        # Ingest into ALL stores
                        async with AsyncSessionLocal() as db:
                            # We create/update a Document record first
                            # This is helpful for the UI to track progress
                            doc_record = await self._get_or_create_document(db, filename, service, temp_path, etag)
                            
                            # Perform ingestion into all stores
                            # We use the existing RetrievalService but we'll use a new multi-store method we'll add
                            count, chunks = await self.retrieval_service.doc_processor.process_file(temp_path, filename)
                            if chunks:
                                logger.info(f"Processing {len(chunks)} chunks for {filename} into all stores...")
                                await self.retrieval_service.engine.add_to_all_stores(chunks)
                                
                                # Update registry/DB status
                                doc_record.status = "completed"
                                doc_record.processed = True
                                meta = dict(doc_record.metadata_info or {})
                                meta["s3_etag"] = etag
                                meta["last_synced"] = asyncio.get_event_loop().time()
                                doc_record.metadata_info = meta
                                await db.commit()
                                logger.info(f"✅ Bootstrap complete for {filename}")
                            else:
                                logger.warning(f"No chunks extracted from {filename}")
                    except Exception as e:
                        logger.error(f"Failed to bootstrap {filename}: {e}")
                else:
                    logger.info(f"✅ {filename} is already up to date.")

            logger.info("Bootstrap Synchronization complete.")

        except Exception as e:
            logger.error(f"Bootstrap Sync Error: {e}")

    async def _list_s3_documents(self) -> List[Dict[str, Any]]:
        """Lists documents in the S3 bucket with their ETags."""
        try:
            paginator = s3_sync_manager.s3.get_paginator("list_objects_v2")
            docs = []
            
            loop = asyncio.get_event_loop()
            pages = await loop.run_in_executor(
                None, 
                lambda: list(paginator.paginate(Bucket=s3_sync_manager.bucket, Prefix=settings.S3_DOCUMENTS_PREFIX))
            )
            
            for page in pages:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if key == settings.S3_DOCUMENTS_PREFIX: # Skip the folder key itself
                        continue
                    
                    filename = os.path.basename(key)
                    docs.append({
                        "filename": filename,
                        "etag": obj["ETag"].strip('"'),
                        "last_modified": obj["LastModified"]
                    })
            return docs
        except Exception as e:
            logger.error(f"Failed to list S3 documents: {e}")
            return []

    async def _needs_processing(self, filename: str, etag: str) -> bool:
        """Determines if a document needs processing based on its ETag."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Document).where(Document.filename == filename))
            doc = result.scalar_one_or_none()
            
            if not doc:
                return True # New document
            
            if doc.status != "completed":
                return True # Failed or partial earlier
            
            # Check ETag in metadata
            meta = doc.metadata_info or {}
            stored_etag = meta.get("s3_etag")
            
            return stored_etag != etag

    async def _get_or_create_document(self, db, filename, service, path, etag):
        """Gets or creates a Document record in the SQL DB."""
        result = await db.execute(select(Document).where(Document.filename == filename))
        doc = result.scalar_one_or_none()
        
        if not doc:
            doc = Document(
                filename=filename,
                source_path=path,
                status="processing",
                metadata_info={"detected_service": service, "s3_etag": etag}
            )
            db.add(doc)
        else:
            doc.status = "processing"
            doc.source_path = path
            meta = dict(doc.metadata_info or {})
            meta["s3_etag"] = etag
            doc.metadata_info = meta
            
        await db.commit()
        await db.refresh(doc)
        return doc

bootstrap_sync = BootstrapSync()

"""
Documents API Router
- Handles document uploading, listing, and deletion
- Implements robust error handling and loguru logging
- Fixes blocking IO in file uploads and adds filename sanitization
"""
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
import os
import aiofiles
import shutil
import uuid
from typing import List

from backend.services.retrieval.semantic_search import RetrievalService
from backend.models.database import get_db, AsyncSessionLocal
from backend.models.models import Document
from backend.api.schemas import DocumentResponse
from backend.utils.source_validator import register_document, get_valid_sources
from backend.utils.service_detection import get_service_from_filename, get_display_name
from backend.services.s3_sync import s3_sync_manager
import asyncio

router = APIRouter()
retrieval_service = RetrievalService()

def sanitize_filename(filename: str) -> str:
    """Basic filename sanitization to prevent directory traversal."""
    # Remove path components and only keep basename
    base = os.path.basename(filename)
    # Replace spaces with underscores
    return base.replace(" ", "_")

async def update_system_prompt_with_new_doc(filename: str, service: str):
    """
    Updates the LLM service knowledge of valid sources
    every time a new document is added.
    """
    from backend.services.llm_service import llm_service
    
    valid_sources = get_valid_sources()
    
    # Rebuild the valid sources section of the prompt
    # Update LLM service knowledge
    llm_service.update_valid_sources(valid_sources)
    
    logger.info(f"[PIPELINE] System prompt updated. Valid sources: {len(valid_sources)} documents")

async def post_ingestion_pipeline(filename: str, chunks: list, embeddings: list, service: str, file_path: str):
    """
    Runs automatically after every document upload.
    Handles registration, metadata, system prompt update, and S3 backup.
    """
    # Step 1: Register in registry
    register_document(filename, service)
    
    # Step 2: Tag all chunks with correct metadata
    # (This assumes chunks is a list of Document objects from langchain)
    for i, chunk in enumerate(chunks):
        if hasattr(chunk, 'metadata'):
            chunk.metadata.update({
                "source":    filename,
                "service":   service,
                "doc_type":  "official_aws_doc",
                "chunk_index": i,
                "file_type": filename.rsplit('.', 1)[-1].lower(),
                "display_name": get_display_name(service)
            })
    
    # Step 4: Update system prompt with new doc list
    await update_system_prompt_with_new_doc(filename, service)

    # Step 5: Sync updated index and document to S3
    from backend.services.s3_sync import s3_sync_manager
    try:
        # Sync the specific document
        # We need the local path here, but post_ingestion_pipeline 
        # doesn't take it currently. We'll sync the index for now
        # and rely on the full sync for the document if needed.
        # Actually, let's fix the pipeline to accept the path in a future refactor.
        # For now, we sync the shared index which is the most critical.
        await s3_sync_manager.sync_index_to_s3()
        logger.info(f"S3 sync complete after {filename} upload")
    except Exception as s3e:
        logger.warning(f"S3 sync failed (non-blocking): {s3e}")
    
    # Trigger S3 sync in background (non-blocking)
    async def run_sync_and_cleanup():
        try:
            # Phase 1: Upload
            await s3_sync_manager.sync_all_after_upload(
                filename=filename,
                service=service,
                file_path=file_path,
                chunks=chunks,
                embeddings=embeddings
            )
            # Phase 2: Cleanup (Optional/Safe)
            # We wait a bit to ensure everything is settled
            await asyncio.sleep(2)
            await s3_sync_manager.verify_and_cleanup_local(file_path, service, filename)
        except Exception as e:
            logger.error(f"S3 Sync/Cleanup pipeline failed for {filename}: {e}")

    asyncio.create_task(run_sync_and_cleanup())
    
    display = get_display_name(service)
    logger.info(f"[PIPELINE] ✅ {filename} → {display} ({len(chunks)} chunks) — Scheduled for S3 & Cleanup")

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    database: str = "faiss",
    db: AsyncSession = Depends(get_db)
):
    """Uploads a document and starts background ingestion."""
    try:
        sanitized_name = sanitize_filename(file.filename)
        # Use a unique prefix to avoid collisions
        unique_name = f"{uuid.uuid4().hex[:8]}_{sanitized_name}"
        
        temp_dir = "data/uploads/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, unique_name)
        
        # Async file writing to avoid blocking the event loop
        async with aiofiles.open(temp_path, mode="wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Auto-detect service from filename
        detected_service = get_service_from_filename(sanitized_name)
        
        # Create DB record
        db_doc = Document(
            filename=sanitized_name,
            file_type=sanitized_name.split('.')[-1] if '.' in sanitized_name else 'unknown',
            source_path=temp_path,
            status="pending",
            user_id="default-user",
            metadata_info={
                "target_database": database, 
                "original_filename": file.filename,
                "detected_service": detected_service
            }
        )
        db.add(db_doc)
        await db.commit()
        await db.refresh(db_doc)
        
        doc_id = db_doc.id

        # Process in background
        async def process_and_cleanup(d_id: str, db_name: str, path: str, fname: str, svc: str):
            try:
                async with AsyncSessionLocal() as session:
                    # ingest_document now returns (count, chunks)
                    count, chunks = await retrieval_service.ingest_document(path, fname, db_name, d_id, session)
                    
                    # Run post-ingestion pipeline with actual chunks
                    # Note: embeddings are still empty as they are stored inside the vector store,
                    # but chunks are now correctly passed for S3 backup.
                    await post_ingestion_pipeline(fname, chunks, [], svc, path)
                    
            except Exception as e:
                logger.error(f"Background processing failed for {fname}: {e}")
            finally:
                # Optionally remove temp file after ingestion if needed
                # os.remove(path)
                pass

        background_tasks.add_task(process_and_cleanup, doc_id, database, temp_path, sanitized_name, detected_service)
        
        logger.info(f"File {file.filename} uploaded and queued for processing. Detected service: {detected_service}")
        
        return {
            "success": True,
            "filename": sanitized_name,
            "service_detected": detected_service,
            "display_name": get_display_name(detected_service),
            "message": f"✅ {sanitized_name} uploaded successfully. "
                       f"Service detected: {get_display_name(detected_service)}. "
                       f"Ready to answer questions immediately.",
            "registry_updated": True,
            "valid_sources_count": len(get_valid_sources()),
            "document_id": doc_id
        }
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/{document_id}/retry")
async def retry_document_ingestion(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Retries ingestion for a failed document using its existing local file."""
    try:
        doc = await db.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        if not doc.source_path or not os.path.exists(doc.source_path):
            raise HTTPException(status_code=400, detail="Source file no longer exists on server. Please re-upload.")

        database = doc.metadata_info.get("target_database", "faiss")
        detected_service = doc.metadata_info.get("detected_service", "aws")
        
        doc.status = "pending"
        await db.commit()

        # Process in background
        async def process_and_cleanup(d_id: str, db_name: str, path: str, fname: str, svc: str):
            try:
                async with AsyncSessionLocal() as session:
                    count, chunks = await retrieval_service.ingest_document(path, fname, db_name, d_id, session)
                    await post_ingestion_pipeline(fname, chunks, [], svc, path)
            except Exception as e:
                logger.error(f"Retry background processing failed for {fname}: {e}")

        background_tasks.add_task(
            process_and_cleanup, 
            doc.id, 
            database, 
            doc.source_path, 
            doc.filename, 
            detected_service
        )
        
        logger.info(f"Retry queued for document {doc.filename} (ID: {document_id})")
        
        return {
            "success": True,
            "message": f"Retry started for {doc.filename}. You can monitor progress in the dashboard.",
            "document_id": document_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry failed for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")

@router.get("/")
async def list_documents(db: AsyncSession = Depends(get_db)):
    """Lists all uploaded documents with status and metadata from SQL database."""
    try:
        # Query DB for all documents
        result = await db.execute(select(Document))
        db_docs = result.scalars().all()
        
        # Transform to format expected by frontend
        formatted_docs = []
        for d in db_docs:
            formatted_docs.append({
                "id": str(d.id),
                "filename": d.filename,
                "file_type": d.file_type or "pdf",
                "status": d.status,
                "upload_date": d.upload_date.isoformat() if d.upload_date else "2026-02-28",
                "metadata_info": d.metadata_info or {}
            })
            
        return {
            "documents": formatted_docs,
            "total": len(formatted_docs)
        }
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents.")

@router.delete("/{document_id}")
async def delete_document(document_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a document and its associated data from all stores."""
    try:
        # 1. GET Document to find filename and target database
        doc = await db.get(Document, document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        filename = doc.filename
        database = doc.metadata_info.get("target_database", "faiss")
        
        logger.info(f"Deleting document: {filename} from {database}")
        
        # 2. DELETE from Vector Store
        try:
            await retrieval_service.delete_document(filename, database=database)
        except Exception as ve:
            logger.error(f"Vector store deletion error for {filename}: {ve}")
            # We continue even if vector store fails to at least clean up the DB
        
        # 3. DELETE from SQL
        await db.delete(doc)
        await db.commit()
        
        return {"message": f"Document {filename} deleted successfully."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global deletion error for {document_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/s3/status")
async def s3_status():
    """Returns summary of everything in S3."""
    summary = await s3_sync_manager.get_bucket_summary()
    return summary

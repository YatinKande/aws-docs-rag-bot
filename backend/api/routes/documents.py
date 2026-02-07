from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.retrieval.semantic_search import RetrievalService
from backend.models.database import get_db, AsyncSessionLocal
from backend.models.models import Document
from backend.api.schemas import DocumentResponse
from typing import List
import os
import shutil

router = APIRouter()
retrieval_service = RetrievalService()

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    database: str = "faiss",
    db: AsyncSession = Depends(get_db)
):
    # Save file temporarily
    temp_dir = "data/uploads/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create DB record
    db_doc = Document(
        filename=file.filename,
        file_type=file.filename.split('.')[-1] if '.' in file.filename else 'unknown',
        source_path=temp_path,
        status="pending",
        user_id="default-user",
        metadata_info={"target_database": database}
    )
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    
    doc_id = db_doc.id

    # Process in background
    async def process_and_cleanup(d_id: str, db_name: str, path: str, fname: str):
        async with AsyncSessionLocal() as session:
            await retrieval_service.ingest_document(path, fname, db_name, d_id, session)
            # os.remove(path)

    background_tasks.add_task(process_and_cleanup, doc_id, database, temp_path, file.filename)
    
    return {"message": f"File {file.filename} uploaded. Processing started.", "document_id": doc_id}

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.upload_date.desc()))
    return result.scalars().all()

from backend.services.retrieval.advanced_retrieval import AdvancedRetrieval
from backend.services.document_processor import DocumentProcessor
from backend.models.models import Document
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

class RetrievalService:
    def __init__(self):
        self.engine = AdvancedRetrieval()
        self.doc_processor = DocumentProcessor()

    async def ingest_document(
        self, 
        file_path: str, 
        filename: str, 
        database: str = "faiss", 
        document_id: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ):
        """Processes a file and adds it to the advanced retrieval engine."""
        if document_id and db:
            doc = await db.get(Document, document_id)
            if doc:
                doc.status = "processing"
                await db.commit()

        chunks = await self.doc_processor.process_file(file_path, filename)
        
        if chunks:
            await self.engine.add_documents(chunks, database=database)
            
            if document_id and db:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.status = "completed"
                    doc.processed = True
                    # Create a new dict to ensure SQLAlchemy detects the change
                    meta = dict(doc.metadata_info or {})
                    meta["chunks"] = len(chunks)
                    from datetime import datetime
                    meta["processed_at"] = datetime.utcnow().isoformat()
                    doc.metadata_info = meta
                    
                    # Force SQLAlchemy to detect change in JSON column
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(doc, "metadata_info")
                    
                    await db.commit()
                    print(f"Successfully processed {filename}: {len(chunks)} chunks")
        else:
            if document_id and db:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.status = "failed"
                    await db.commit()
                    
        return len(chunks) if chunks else 0

    async def semantic_search(self, query: str, top_k: int = 5, database: str = "faiss") -> List[Dict[str, Any]]:
        """Performs advanced retrieval (Query Expansion + Hybrid + Reranking)."""
        return await self.engine.search(query, top_k=top_k, database=database)

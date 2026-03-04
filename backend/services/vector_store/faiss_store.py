"""
FAISS Vector Store Service
- Implements async wrappers for blocking FAISS operations
- Robust error handling and loguru logging
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_community.vectorstores import FAISS

from backend.services.embeddings import get_shared_embeddings
from backend.services.vector_store.base import VectorStoreBase

class FAISSStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = get_shared_embeddings()
        self.index_path = "data/indexes/faiss"
        self.vector_store = None
        # We don't block constructor, but _load_or_create is synchronous in LangChain
        # We'll handle it carefully when first used if needed, or just let it init.
        self._load_or_create()

    def _load_or_create(self):
        """Loads index from disk if it exists."""
        try:
            if os.path.exists(self.index_path):
                self.vector_store = FAISS.load_local(
                    self.index_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                    distance_strategy="COSINE"
                )
                logger.info(f"FAISS index loaded from {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to FAISS asynchronously."""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            def _sync_add():
                if self.vector_store:
                    self.vector_store.add_texts(texts, metadatas=metadatas)
                else:
                    self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas, distance_strategy="COSINE")
                self.vector_store.save_local(self.index_path)

            await asyncio.get_event_loop().run_in_executor(None, _sync_add)
            logger.info(f"Added {len(documents)} chunks to FAISS.")
        except Exception as e:
            logger.error(f"Failed to add documents to FAISS: {e}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches FAISS asynchronously."""
        if not self.vector_store:
            return []
            
        try:
            # Define synchronous search to run in executor
            def _sync_search():
                # Handle multi-value filters manually if needed, otherwise use metadata filter
                # Note: LangChain FAISS metadata filtering is simple.
                return self.vector_store.similarity_search_with_score(query, k=top_k, filter=filter)

            docs_with_scores = await asyncio.get_event_loop().run_in_executor(None, _sync_search)
            
            results = []
            for doc, score in docs_with_scores:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                })
            return results
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from FAISS asynchronously."""
        if not self.vector_store:
            return

        try:
            def _sync_delete():
                ids_to_delete = []
                for doc_id, doc in self.vector_store.docstore._dict.items():
                    match = True
                    for key, value in filter_dict.items():
                        if doc.metadata.get(key) != value:
                            match = False
                            break
                    if match:
                        ids_to_delete.append(doc_id)
                
                if ids_to_delete:
                    self.vector_store.delete(ids_to_delete)
                    self.vector_store.save_local(self.index_path)
                    return len(ids_to_delete)
                return 0

            deleted_count = await asyncio.get_event_loop().run_in_executor(None, _sync_delete)
            if deleted_count > 0:
                logger.info(f"Deleted {deleted_count} chunks from FAISS matching {filter_dict}")
        except Exception as e:
            logger.error(f"Failed to delete documents from FAISS: {e}")

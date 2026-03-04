"""
Chroma Vector Store Service
- Implements async wrappers for blocking Chroma operations
- Robust error handling and loguru logging
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_chroma import Chroma

from backend.services.embeddings import get_shared_embeddings
from backend.services.vector_store.base import VectorStoreBase

class ChromaStore(VectorStoreBase):
    def __init__(self):
        try:
            self.embeddings = get_shared_embeddings()
            self.persist_directory = "data/indexes/chroma"
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
                collection_name="rag_docs",
                collection_metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaStore initialized at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaStore: {e}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to Chroma asynchronously."""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            def _sync_add():
                self.vector_store.add_texts(texts, metadatas=metadatas)
                
            await asyncio.get_event_loop().run_in_executor(None, _sync_add)
            logger.info(f"Added {len(documents)} chunks to Chroma.")
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma: {e}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches Chroma asynchronously."""
        try:
            def _sync_search():
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
            logger.error(f"Chroma search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from Chroma asynchronously."""
        try:
            source = filter_dict.get("source")
            if not source:
                logger.warning("Chroma deletion requires a 'source' filter.")
                return

            def _sync_delete():
                self.vector_store.delete(where={"source": source})
                return True

            await asyncio.get_event_loop().run_in_executor(None, _sync_delete)
            logger.info(f"Deleted documents with source '{source}' from Chroma")
        except Exception as e:
            logger.error(f"Failed to delete documents from Chroma: {e}")

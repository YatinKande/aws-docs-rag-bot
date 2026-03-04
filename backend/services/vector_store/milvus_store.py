"""
Milvus Vector Store Service
- Implements async wrappers for blocking Milvus operations
- Robust error handling and loguru logging
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from langchain_milvus import Milvus

from backend.services.embeddings import get_shared_embeddings
from backend.services.vector_store.base import VectorStoreBase

class MilvusStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = get_shared_embeddings()
        self.collection_name = "rag_docs"
        self.connection_args = {"uri": "./milvus_demo.db"} # Milvus Lite
        self.vector_store = None

    def _get_vector_store(self):
        """Lazy initialization of Milvus store."""
        if self.vector_store is None:
            try:
                self.vector_store = Milvus(
                    embedding_function=self.embeddings,
                    connection_args=self.connection_args,
                    collection_name=self.collection_name,
                    auto_id=True
                )
                logger.info("Milvus (Lite) initialized.")
            except Exception as e:
                logger.error(f"Milvus initialization error: {e}")
                raise
        return self.vector_store

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to Milvus asynchronously."""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            def _sync_add():
                store = self._get_vector_store()
                store.add_texts(texts, metadatas=metadatas)

            await asyncio.get_event_loop().run_in_executor(None, _sync_add)
            logger.info(f"Added {len(documents)} chunks to Milvus.")
        except Exception as e:
            logger.error(f"Failed to add documents to Milvus: {e}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches Milvus asynchronously."""
        try:
            def _sync_search():
                store = self._get_vector_store()
                return store.similarity_search_with_score(query, k=top_k, filter=filter)

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
            logger.error(f"Milvus search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from Milvus based on metadata."""
        try:
            source = filter_dict.get("source")
            if not source:
                logger.warning("Milvus deletion requires a 'source' filter.")
                return

            def _sync_delete():
                store = self._get_vector_store()
                if hasattr(store, 'col'):
                    store.col.delete(f"source == '{source}'")
                    return True
                else:
                    logger.warning("Milvus deletion not supported in this wrapper version.")
                    return False

            await asyncio.get_event_loop().run_in_executor(None, _sync_delete)
            logger.info(f"Deleted documents with source '{source}' from Milvus")
        except Exception as e:
            logger.error(f"Milvus delete error: {e}")

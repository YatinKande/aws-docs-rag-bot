"""
Qdrant Vector Store Service
- Implements async wrappers for blocking Qdrant operations
- Robust error handling and loguru logging
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore

from backend.services.embeddings import get_shared_embeddings
from backend.services.vector_store.base import VectorStoreBase

class QdrantStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = get_shared_embeddings()
        self.collection_name = "rag_docs"
        self.path = "qdrant_db"
        self.vector_store = None

    def _get_vector_store(self):
        """Lazy initialization of Qdrant store."""
        if self.vector_store is None:
            try:
                client = QdrantClient(path=self.path)
                self.vector_store = QdrantVectorStore(
                    client=client,
                    collection_name=self.collection_name,
                    embedding=self.embeddings
                )
                logger.info(f"Qdrant initialized at {self.path}")
            except Exception as e:
                logger.error(f"Qdrant initialization error: {e}")
                raise
        return self.vector_store

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to Qdrant asynchronously."""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            def _sync_add():
                store = self._get_vector_store()
                store.add_texts(texts, metadatas=metadatas)

            await asyncio.get_event_loop().run_in_executor(None, _sync_add)
            logger.info(f"Added {len(documents)} chunks to Qdrant.")
        except Exception as e:
            logger.error(f"Failed to add documents to Qdrant: {e}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches Qdrant asynchronously."""
        try:
            def _sync_search():
                store = self._get_vector_store()
                # Use similarity_search to avoid potential client attribute issues with scoring if version mismatch
                return store.similarity_search(query, k=top_k, filter=filter)

            docs = await asyncio.get_event_loop().run_in_executor(None, _sync_search)
            
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": 0.5 # Default score if not provided
                })
            return results
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from Qdrant based on metadata."""
        try:
            source = filter_dict.get("source")
            if not source:
                logger.warning("Qdrant deletion requires a 'source' filter.")
                return

            def _sync_delete():
                store = self._get_vector_store()
                store.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="metadata.source",
                                    match=models.MatchValue(value=source),
                                )
                            ]
                        )
                    )
                )
                return True

            await asyncio.get_event_loop().run_in_executor(None, _sync_delete)
            logger.info(f"Deleted documents with source '{source}' from Qdrant")
        except Exception as e:
            logger.error(f"Qdrant delete error: {e}")

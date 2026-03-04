"""
LanceDB Vector Store Service
- Implements async wrappers for blocking LanceDB operations
- Robust error handling and loguru logging
"""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
import lancedb
from langchain_community.vectorstores import LanceDB

from backend.services.embeddings import get_shared_embeddings
from backend.services.vector_store.base import VectorStoreBase

class LanceDBStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = get_shared_embeddings()
        self.uri = "lancedb_data"
        self.table_name = "rag_docs"
        self.db = None
        self.vector_store = None

    def _get_db(self):
        """Lazy connection to LanceDB."""
        if self.db is None:
            try:
                self.db = lancedb.connect(self.uri)
            except Exception as e:
                logger.error(f"Failed to connect to LanceDB at {self.uri}: {e}")
                raise
        return self.db

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Adds documents to LanceDB asynchronously."""
        try:
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            def _sync_add():
                if self.vector_store is None:
                    self.vector_store = LanceDB.from_texts(
                        texts, 
                        self.embeddings, 
                        connection=self._get_db(),
                        table_name=self.table_name,
                        metadatas=metadatas
                    )
                else:
                    self.vector_store.add_texts(texts, metadatas=metadatas)

            await asyncio.get_event_loop().run_in_executor(None, _sync_add)
            logger.info(f"Added {len(documents)} chunks to LanceDB.")
        except Exception as e:
            logger.error(f"Failed to add documents to LanceDB: {e}")

    async def search(self, query: str, top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Searches LanceDB asynchronously."""
        try:
            def _sync_search():
                if self.vector_store is None:
                    # Try to load existing table
                    try:
                        self.vector_store = LanceDB(
                            self._get_db(),
                            self.embeddings,
                            table_name=self.table_name
                        )
                    except:
                        return []
                
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
            logger.error(f"LanceDB search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any]):
        """Delete documents from LanceDB based on metadata."""
        try:
            source = filter_dict.get("source")
            if not source:
                logger.warning("LanceDB deletion requires a 'source' filter.")
                return

            def _sync_delete():
                db = self._get_db()
                table = db.open_table(self.table_name)
                table.delete(f"source == '{source}'")
                return True

            await asyncio.get_event_loop().run_in_executor(None, _sync_delete)
            logger.info(f"Deleted documents with source '{source}' from LanceDB")
        except Exception as e:
            logger.error(f"LanceDB delete error: {e}")

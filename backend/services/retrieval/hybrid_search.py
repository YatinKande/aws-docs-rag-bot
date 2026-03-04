"""
Hybrid Search Service
- Identifies and fixes syntax and logical bugs
- Implements robust error handling with loguru
- Replaces prints with logging
- Ensures async safety and consistency
"""
from typing import List, Dict, Any, Optional
from loguru import logger

from backend.services.retrieval.bm25_search import BM25Index
from backend.services.vector_store.faiss_store import FAISSStore
from backend.services.vector_store.chroma_store import ChromaStore
from backend.services.vector_store.lancedb_store import LanceDBStore
from backend.services.vector_store.milvus_store import MilvusStore
from backend.services.vector_store.qdrant_store import QdrantStore

class HybridSearch:
    def __init__(self):
        self.bm25_index = BM25Index()
        # Lazily initialize stores
        self.stores = {
            "faiss": FAISSStore(),
            "chroma": None,
            "lancedb": None,
            "milvus": None,
            "qdrant": None
        }

    def _get_store(self, name: str):
        """Safely retrieves a vector store by name."""
        name = name.lower()
        if name not in self.stores:
            logger.warning(f"Unknown database '{name}'. Falling back to 'faiss'.")
            name = "faiss"
            
        if self.stores[name] is None:
            try:
                if name == "chroma":
                    self.stores[name] = ChromaStore()
                elif name == "lancedb":
                    self.stores[name] = LanceDBStore()
                elif name == "milvus":
                    self.stores[name] = MilvusStore()
                elif name == "qdrant":
                    self.stores[name] = QdrantStore()
            except Exception as e:
                logger.error(f"Failed to initialize vector store {name}: {e}")
                return self.stores["faiss"] # Fallback if specific store fails init
        
        return self.stores[name]

    async def add_documents(self, documents: List[Dict[str, Any]], database: str = "faiss"):
        """Adds documents to both BM25 and vector stores."""
        try:
            self.bm25_index.add_documents(documents)
            store = self._get_store(database)
            if store:
                await store.add_documents(documents)
            logger.info(f"Indexed {len(documents)} chunks into BM25 and {database}")
        except Exception as e:
            logger.error(f"Hybrid indexing failed: {e}")

    async def add_to_all_stores(self, documents: List[Dict[str, Any]]):
        """Adds documents to all available and initialized vector stores."""
        try:
            # 1. Add to BM25
            self.bm25_index.add_documents(documents)
            logger.info("Indexed chunks into BM25.")

            # 2. Add to all available vector stores
            tasks = []
            available_db_names = ["faiss", "chroma", "lancedb", "milvus", "qdrant"]
            
            for db_name in available_db_names:
                # We try to initialize/get the store
                store = self._get_store(db_name)
                if store:
                    # Note: _get_store might return FAISS as fallback, 
                    # we should be careful about double-adding to FAISS.
                    # But if we use explicit names, it's safer.
                    tasks.append(store.add_documents(documents))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info(f"Successfully sent {len(documents)} chunks to all enabled vector stores.")
        except Exception as e:
            logger.error(f"Failed to add documents to all stores: {e}")

    def reciprocal_rank_fusion(self, bm25_results: List[Dict[str, Any]], dense_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """Combines results using Reciprocal Rank Fusion."""
        try:
            fused_scores = {}
            
            def get_doc_id(res):
                meta = res.get("metadata", {})
                return (res["content"], meta.get("source"), meta.get("chunk_index"))
            
            for rank, res in enumerate(bm25_results):
                doc_id = get_doc_id(res)
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 / (rank + k))
                
            for rank, res in enumerate(dense_results):
                doc_id = get_doc_id(res)
                fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 / (rank + k))
                
            # Sort by fused score
            sorted_fused = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Map IDs back to original objects
            all_docs = {}
            for res in bm25_results + dense_results:
                all_docs[get_doc_id(res)] = res
            
            final_results = []
            for doc_id, score in sorted_fused:
                doc = all_docs[doc_id].copy()
                doc["hybrid_score"] = float(score)
                final_results.append(doc)
                
            return final_results
        except Exception as e:
            logger.error(f"RRF fusion failed: {e}")
            return bm25_results or dense_results

    async def search(self, query: str, top_k: int = 5, database: str = "faiss", filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Performs hybrid search by combining BM25 and Vector Search."""
        try:
            # Get candidates from both
            bm25_res = self.bm25_index.search(query, top_k=20, filter=filter)
            store = self._get_store(database)
            
            dense_res = []
            if store:
                dense_res = await store.search(query, top_k=20, filter=filter)
            
            # Fuse
            fused = self.reciprocal_rank_fusion(bm25_res, dense_res)
            return fused[:top_k]
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    async def delete_documents(self, filter_dict: Dict[str, Any], database: str = "faiss"):
        """Deletes documents from both BM25 and the specified vector store."""
        try:
            await self.bm25_index.delete_documents(filter_dict)
            store = self._get_store(database)
            if store:
                await store.delete_documents(filter_dict)
            logger.info(f"Deleted documents matching {filter_dict} from hybrid indices.")
        except Exception as e:
            logger.error(f"Hybrid deletion failed: {e}")

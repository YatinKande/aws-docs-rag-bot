"""
Advanced Retrieval Service
- Orchestrates Hybrid Search and Reranking
- Implements robust error handling with loguru
"""
from typing import List, Dict, Any, Optional
from loguru import logger
from backend.services.retrieval.hybrid_search import HybridSearch
from backend.services.retrieval.reranker import Reranker

class AdvancedRetrieval:
    def __init__(self):
        try:
            self.hybrid_search = HybridSearch()
            self.reranker = Reranker()
            logger.info("AdvancedRetrieval initialized successfully.")
        except Exception as e:
            logger.error(f"AdvancedRetrieval initialization failed: {e}")
            raise

    async def search(self, query: str, top_k: int = 5, database: str = "faiss", filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Performs multi-stage retrieval: Hybrid Search -> Reranking."""
        try:
            # Stage 1 & 2: Hybrid Search (BM25 + Dense)
            candidates = await self.hybrid_search.search(query, top_k=20, database=database, filter=filter)
            
            if not candidates:
                logger.info(f"No candidates found for query: {query}")
                return []
                
            # Stage 3: Reranking
            final_results = await self.reranker.rerank(query, candidates, top_k=top_k)
            return final_results
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return []

    async def add_documents(self, documents: List[Dict[str, Any]], database: str = "faiss"):
        """Proxies document addition to hybrid search."""
        try:
            await self.hybrid_search.add_documents(documents, database=database)
        except Exception as e:
            logger.error(f"AdvancedRetrieval add_documents failed: {e}")

    async def delete_documents(self, filter_dict: Dict[str, Any], database: str = "faiss"):
        """Proxies document deletion to hybrid search."""
        try:
            await self.hybrid_search.delete_documents(filter_dict, database=database)
        except Exception as e:
            logger.error(f"AdvancedRetrieval delete_documents failed: {e}")

    async def add_to_all_stores(self, documents: List[Dict[str, Any]]):
        """Proxies batch ingestion to all stores."""
        try:
            await self.hybrid_search.add_to_all_stores(documents)
        except Exception as e:
            logger.error(f"AdvancedRetrieval add_to_all_stores failed: {e}")

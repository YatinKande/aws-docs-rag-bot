from typing import List, Dict, Any
from backend.services.retrieval.hybrid_search import HybridSearch
from backend.services.retrieval.reranker import Reranker

class AdvancedRetrieval:
    def __init__(self):
        self.hybrid_search = HybridSearch()
        self.reranker = Reranker()

    async def search(self, query: str, top_k: int = 5, database: str = "faiss") -> List[Dict[str, Any]]:
        # Stage 1 & 2: Hybrid Search (BM25 + Dense)
        candidates = await self.hybrid_search.search(query, top_k=20, database=database)
        
        # Stage 3: Reranking
        final_results = await self.reranker.rerank(query, candidates, top_k=top_k)
        return final_results

    async def add_documents(self, documents: List[Dict[str, Any]], database: str = "faiss"):
        await self.hybrid_search.add_documents(documents, database=database)

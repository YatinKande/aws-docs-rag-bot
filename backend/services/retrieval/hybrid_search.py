from typing import List, Dict, Any
from backend.services.retrieval.bm25_search import BM25Index
from backend.services.vector_store.faiss_store import FAISSStore
from backend.services.vector_store.chroma_store import ChromaStore
from backend.services.vector_store.lancedb_store import LanceDBStore
from backend.services.vector_store.milvus_store import MilvusStore
from backend.services.vector_store.qdrant_store import QdrantStore

class HybridSearch:
    def __init__(self):
        self.bm25_index = BM25Index()
        # Lazily initialize stores or manage multiple? 
        # For simplicity in this demo, we'll keep a mapping
        self.stores = {
            "faiss": FAISSStore(),
            "chroma": None,
            "lancedb": None,
            "milvus": None,
            "qdrant": None
        }

    def _get_store(self, name: str):
        name = name.lower()
        if name not in self.stores:
            print(f"Warning: Unknown database '{name}'. Falling back to 'faiss'.")
            name = "faiss"
            
        if self.stores[name] is None:
            if name == "chroma":
                self.stores[name] = ChromaStore()
            elif name == "lancedb":
                self.stores[name] = LanceDBStore()
            elif name == "milvus":
                self.stores[name] = MilvusStore()
            elif name == "qdrant":
                self.stores[name] = QdrantStore()
        
        return self.stores[name]

    async def add_documents(self, documents: List[Dict[str, Any]], database: str = "faiss"):
        self.bm25_index.add_documents(documents)
        store = self._get_store(database)
        await store.add_documents(documents)
        print(f"Indexed {len(documents)} chunks into {database}")

    def reciprocal_rank_fusion(self, bm25_results: List[Dict[str, Any]], dense_results: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
        """Combines results using Reciprocal Rank Fusion."""
        fused_scores = {}
        
        for rank, res in enumerate(bm25_results):
            doc_id = res["content"] # Using content as ID for simplicity in MVP
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 / (rank + k))
            
        for rank, res in enumerate(dense_results):
            doc_id = res["content"]
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + (1 / (rank + k))
            
        # Sort by fused score
        sorted_fused = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Reconstruct result objects
        all_docs = {res["content"]: res for res in bm25_results + dense_results}
        
        final_results = []
        for doc_id, score in sorted_fused:
            doc = all_docs[doc_id].copy()
            doc["hybrid_score"] = score
            final_results.append(doc)
            
        return final_results

    async def search(self, query: str, top_k: int = 5, database: str = "faiss") -> List[Dict[Dict[str, Any], Any]]:
        # Get candidates from both
        bm25_res = self.bm25_index.search(query, top_k=20)
        store = self._get_store(database)
        dense_res = await store.search(query, top_k=20)
        
        # Fuse
        fused = self.reciprocal_rank_fusion(bm25_res, dense_res)
        return fused[:top_k]

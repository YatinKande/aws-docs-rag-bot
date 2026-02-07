from typing import List, Dict, Any
from langchain_milvus import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings
from backend.services.vector_store.base import VectorStoreBase
from backend.core.config import settings

class MilvusStore(VectorStoreBase):
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.collection_name = "rag_docs"
        self.connection_args = {"uri": "./milvus_demo.db"} # Milvus Lite
        
        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args=self.connection_args,
            collection_name=self.collection_name,
            auto_id=True,
            index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT", "params": {"nlist": 128}}
        )

    async def add_documents(self, documents: List[Dict[str, Any]]):
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        self.vector_store.add_texts(texts, metadatas=metadatas)

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Milvus search might return different score types, normalize if needed
        docs = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        results = []
        for doc, score in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
        return results
